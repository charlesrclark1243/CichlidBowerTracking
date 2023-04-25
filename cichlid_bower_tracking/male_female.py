import cv2, os, pdb, sys
from cichlid_bower_tracking.helper_modules.file_manager import FileManager as FM
from torch.utils.data import Dataset, DataLoader
import pandas as pd 

# This code ensures that modules can be found in their relative directories
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

class MaleFemaleDataLoader(Dataset):
    def __init__(self, main_directory):
        self.main_directory = main_directory
        male_videos = os.listdir(main_directory + 'Male/')
        female_videos = os.listdir(main_directory + 'Female/')

        index = 0
        dt = pd.DataFrame(columns = ['video_location','video_index','label'])
        for m_video in male_videos:
            new_data = {'video_location':[], 'video_index': [], 'label':[]}
            cap = cv2.VideoCapture(main_directory + 'Male/' + m_video)
            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            video_location = main_directory + 'Male/' + m_video
            for i in range(frames):
                print(index)
                new_data['video_location'].append(video_location)
                new_data['video_index'].append(i)
                new_data['label'] = 'm'
                index += 1
            pdb.set_trace()
        for f_video in female_videos:
            cap = cv2.VideoCapture(main_directory + 'Female/' + f_video)
            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
            video_location = main_directory + 'Female/' + f_video
            for i in range(frames):
                dt.loc[index] = [video_location,i,'f']
                index += 1
        
        pdb.set_trace()


        file_list = glob.glob(self.imgs_path + "*")
        print(file_list)
        self.data = []
        for class_path in file_list:
            class_name = class_path.split("/")[-1]
            for img_path in glob.glob(class_path + "/*.jpeg"):
                self.data.append([img_path, class_name])
        print(self.data)
        self.class_map = {"dogs" : 0, "cats": 1}
        self.img_dim = (416, 416)
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        img_path, class_name = self.data[idx]
        img = cv2.imread(img_path)
        img = cv2.resize(img, self.img_dim)
        class_id = self.class_map[class_name]
        img_tensor = torch.from_numpy(img)
        img_tensor = img_tensor.permute(2, 0, 1)
        class_id = torch.tensor([class_id])
        return img_tensor, class_id

fm_obj = FM('PatrickTesting')

mf_obj = MaleFemaleDataLoader(fm_obj.localMaleFemalesVideosDir)