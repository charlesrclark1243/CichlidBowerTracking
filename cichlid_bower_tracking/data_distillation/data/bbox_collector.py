# from torchvision.transforms.functional import rotate, resize, InterpolationMode
from torchvision.io import read_video 
from torchvision.utils import save_image
from typing import Dict
import numpy as np
import pandas as pd
import torch
import math, os, json

np.random.seed(0)

# from "sort_detections.py"...
IMG_W = 1296
IMG_H = 972

# hyperparams...
# RESZ_DIM = 100

class BBoxCollector:
    def __init__(self, video_file: str, detections_file: str, bboxes_dir: str, dim=128, filename=None):
        '''
        Create and initialize an instance of the BBoxCollector class.

        Inputs:
            video_file: a string value representing the filepath of the video which will be processed.
            detections_file: a path to the file containing the detection data generated by YOLO.
            bboxes_dir: a path to the directory in which the transformed bbox images should be saved.
            dim: an integer value indicating the dimension to be used as each resized bbox's width and height; defaults to 128.
            filename: the desired name for the JSON file; deprecated, defaults to None.
        '''
        
        self.__version__ = '0.4.1'
        self.video_file = video_file
        self.detections_file = detections_file
        self.bboxes_dir = bboxes_dir
        self.dim = dim
        self.filename = filename

        # list to store each collected bbox, organized by frame
        self.bboxes = dict()

    def _get_bbox(self, frame: torch.Tensor, x_center: int, y_center: int, width: int, height: int) -> torch.Tensor:
        '''
        Carves a PyTorch Tensor representing the bounding box centered at (x_center, y_center) with dimensions (width, height) out of the passed
        frame Tensor. The carved out bbox is slightly larger than necessary to ensure the entire fish body remains in the image after rotation.
        Based on Bree's cropping method, which she sent to me via email.

        Inputs:
            frame: a PyTorch Tensor representing a video frame which contains the bbox to be carved out.
            x_center: the x-coordinate of the bbox's center, as calculated during YOLO.
            y_center: the y-coordinate of the bbox's upper-left corner, as calculated during YOLO.
            width: the width of the bbox to be saved, as calculated during YOLO.
            height: the width of the bbox to be saved, as calculated during YOLO.

        Returns: a PyTorch Tensor representing the bbox carved out of the passed frame Tensor.
        '''
        
        # store the longest dimension length like in Bree's cropping method
        max_dim = max(int(width) + 1, int(height) + 1)

        # get bbox coordinates based on Bree's cropping method (PyTorch instead of openCV)
        x_upperleft = int(max(0, x_center - (max_dim)))
        y_upperleft = int(max(0, y_center - (max_dim)))

        x_lowerright = int(max(0, x_center + (max_dim)))
        y_lowerright = int(max(0, y_center + (max_dim)))

        # get and return bbox by slicing passed frame
        bbox = frame[:, x_upperleft:x_lowerright + 1, y_upperleft:y_lowerright + 1]
        
        return bbox

    # def _rotate_bbox(self, bbox: torch.Tensor, x_dot: float, y_dot: float, mode_str='bilinear') -> torch.Tensor:
    #     '''
    #     Rotates the passed in bbox PyTorch Tensor based on the fish's x-dimensional and y-dimensional velocities, as determined by the
    #     Kalman Filter during SORT. Inherently assumes that cichlids only swim in the direction which they are facing with their heads.

    #     Inputs:
    #         bbox: a PyTorch Tensor representing a bounding box, as carved out of a video frame by the self._get_box function; has shape (C, H, W).
    #         x_dot: the x-dimensional velocity as calculated by the Kalman Filter during SORT; listed as u_dot in the tracks data file.
    #         y_dot: the y-dimensional velocoty as calculated by the Kalman Filter during SORT; listed as v_dot in the tracks data file.
    #         mode_str: the interpolation mode to be used during rotation; must be one of {'nearest', 'nearest_exact', 'bilinear'}, but defaults to 'bilinear'.

    #     Returns: A PyTorch Tensor representing the rotated bbox.
    #     '''

    #     # use trig to determine the angle of rotation (convert to degrees)
    #     theta = -math.atan2(y_dot, x_dot) * (180.0 / math.pi)

    #     # define the interpolation mode
    #     if mode_str == 'nearest':
    #         mode = InterpolationMode.NEAREST
    #     elif mode_str == 'nearest_exact':
    #         mode = InterpolationMode.NEAREST_EXACT
    #     else:
    #         mode = InterpolationMode.BILINEAR

    #     # perform rotation and return the resulting bbox
    #     rot_bbox = rotate(bbox, theta, mode)

    #     return rot_bbox
    
    def _resize_bbox(self, bbox: torch.Tensor, mode_str='bilinear') -> torch.Tensor:
        '''
        Resizes the passed bbox PyTorch Tensor to have shape (dim, dim) using the value passed as an instance variable. 

        Inputs:
            bbox: a PyTorch Tensor representing a bounding box, as carved out of a video frame by the self._get_box function; has shape (C, H, W).
            mode_str: the interpolation mode to be used during rotation; must be one of {'nearest', 'nearest_exact', 'bilinear'}, but defaults to 'bilinear'.

        Returns: a PyTorch Tensor representing the resized bbox image.            
        '''

        # define the interpolation mode
        if mode_str == 'nearest':
            mode = InterpolationMode.NEAREST
        elif mode_str == 'nearest_exact':
            mode = InterpolationMode.NEAREST_EXACT
        else:
            mode = InterpolationMode.BILINEAR

        # perform the resize and return the resulting bbox
        resz_bbox = resize(bbox, (self.dim, self.dim), mode)

        return resz_bbox

    def _save_bbox(self, frame_idx: int, frame: torch.Tensor, x_center: int, y_center: int, width: int, height: int, mode_str='bilinear') -> None:
        '''
        Saves the bounding box in the passed video frame with center (x_center, y_center), and dimensions (width, height) to the bboxes 
        dictionary.

        Inputs:
            frame_idx: an integer indicating the frame number from which the bbox will be collected.
            frame: PyTorch Tensor of shape (C, H, W) containing a specific video frame.
            x_center: the x-coordinate of the bbox's center, as calculated during YOLO.
            y_center: the y-coordinate of the bbox's upper-left corner, as calculated during YOLO.
            width: the width of the bbox to be saved, as calculated during YOLO.
            height: the width of the bbox to be saved, as calculated during YOLO.
            mode_str: the interpolation mode to be used during bbox transformation; must be one of {'nearest', 'nearest_exact', 'bilinear'}, but defaults to 'bilinear'.
        '''

        # pass frame through bbox extraction and transformation pipeline
        bbox = self._get_bbox(frame, x_center, y_center, width, height)
        # rot_bbox = self._rotate_bbox(bbox, x_dot, y_dot, mode_str)
        resz_bbox = self._resize_bbox(bbox, mode_str).detach().numpy()
        
        # add bbox to dictionary of collected bboxes and return True to indicate success
        if frame_idx in list(self.bboxes.keys()):
            self.bboxes[frame_idx].append(resz_bbox)
        else:
            self.bboxes[frame_idx] = [resz_bbox]
            
    def _iterate(self, video: torch.Tensor) -> None:
        '''
        Iterates through the passed video Tensor by track ID, saving each bounding box to the bboxes dictionary. Assumes
        that tracking data collected by SortFish class is in sequential order for each track ID.

        Inputs:
            video: PyTorch Tensor of shape (T, C, H, W) containing a video which has already been run through the YOLO + SORT pipeline.
        '''

        # read tracks data from tracks file built by SortFish class
        detections_df = pd.read_csv(self.detections_file)
        detections_df.sort_values(by='frame', ascending=True)

        # iterate by frame
        for _, row in detections_df.iterrows():
            frame_idx = detections_df['frame']

            x1, x2 = row['x1'], row['x2']
            y1, y2 = row['y1'], row['y2']

            width, height = x1 - x2 + 1, y1 - y2 + 1
            x_center, y_center = x2 + (width // 2), y2 + (height // 2)

            self._save_bbox(frame_idx, video[frame_idx, :, :, :], x_center, y_center, width, height)

    # def save_as_json(self) -> bool:
    #     '''
    #     Saves the bboxes dictionary as a JSON file.

    #     Inputs: none.

    #     Returns: a Boolean indicating if the bboxes dictionary was successfully saved as a JSON file.
    #     '''

    #     # save the dictionary as a JSON file when done with iterative saving
    #     with open(f'{self.bboxes_dir}/{self.filename}.json', 'w') as file:
    #         json.dumps(self.bboxes, file)

    #     return True

    def _save_images(self, imgtype='png') -> None:
        '''
        Saves the collected bbox images to individual files in the directory located at self.bboxes_dir.

        Inputs:
            imgtype: the file format to be used in saving the bbox images; defaults to "png".
        '''
        counts = dict()

        for frame_idx, bboxes_list in self.bboxes.items():
            for bbox in bboxes_list:
                assert bbox.shape == (3, self.dim, self.dim)

                if frame_idx in list(self.counts.keys()):
                    counts[frame_idx] += 1
                else:
                    counts[frame_idx] = 1

                bbox_tensor = torch.tensor(bbox, dtype=torch.uint64)
                save_image(bbox_tensor, os.path.join(self.bboxes_dir, f'frame{frame_idx}_n{"0" * (12 - math.floor(1 + math.log10(counts[frame_idx])))}_bbox.{imgtype}'))

    def run(self) -> Dict:
        '''
        Runs the BBoxCollector pipeline.

        Inputs: none.

        Returns: a dictionary with track IDs as keys and lists of bbox images as values, specifically self.bboxes.
        '''
        # Returns: a Boolean indicating that the data distillation preparer was successfully run.

        # handle conversion from self.videoObj to Tensor using the PyTorch read_video function
        video = read_video(self.video_file, output_format='TCHW')

        # iteratively save bboxes to dictionary
        self._iterate(video=video)

        # save each collected bbox to individual PNG files
        self._save_images(imgtype='png')

        # save bboxes dictionary as JSON
        # self.save_as_json()

        # return True

        return self.bboxes
