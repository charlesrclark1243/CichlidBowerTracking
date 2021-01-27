import os, subprocess, pdb, platform
import pandas as pd
from pathlib import Path

class FileManager():
	def __init__(self, projectID = None, modelID = None, rcloneRemote = 'cichlidVideo:', masterDir = 'McGrath/Apps/CichlidPiData'):

		# Identify directory for temporary local files
		if platform.node() == 'raspberrypi' or 'Pi' in platform.node():
			self._identifyPiDirectory()
		else:
			self.localMasterDir = Path.home() / 'Temp' / 'CichlidAnalyzer'

		# Identify cloud directory for rclone
		self.rcloneRemote = rcloneRemote
		# On some computers, the first directory is McGrath, on others it's BioSci-McGrath. Use rclone to figure out which
		output = subprocess.run(['rclone', 'lsf', self.rcloneRemote + masterDir], capture_output = True, encoding = 'utf-8')
		if output.stderr == '':
			self.cloudMasterDir = self.rcloneRemote + masterDir
		else:
			output = subprocess.run(['rclone', 'lsf', self.rcloneRemote + 'BioSci-' + masterDir], capture_output = True, encoding = 'utf-8')
			if output.stderr == '':
				self.cloudMasterDir = self.rcloneRemote + 'BioSci-' + masterDir
			else:
				raise Exception('Cant find master directory (' + masterDir + ') in rclone remote (' + rcloneRemote + ')')

		if projectID is not None:
			self.createProjectData(projectID)

		self.localMLDir = self.localMasterDir / '__MachineLearningModels/'
		if modelID is not None:
			self.createMLData(modelID)
		# Create file names
		self.createPiData()

		# initiate parameters
		self._createParameters()

	def createPiData(self):
		self.localCredentialSpreadsheet = self.localMasterDir / '__CredentialFiles/SAcredentials.json'
		self.localCredentialDrive = self.localMasterDir / '__CredentialFiles/DriveCredentials.txt'

	def createProjectData(self, projectID):
		self.createAnnotationData()
		self.projectID = projectID
		self.localProjectDir = self.localMasterDir / projectID

		# Create logfile
		self.localLogfile = self.localProjectDir / 'Logfile.txt'

		# Data directories created by tracker
		self.localPrepDir = self.localProjectDir / 'PrepFiles'
		self.localFrameDir = self.localProjectDir / 'Frames'
		self.localVideoDir = self.localProjectDir / 'Videos'
		self.localBackupDir = self.localProjectDir / 'Backups'

		# Directories created by analysis
		self.localAnalysisDir = self.localProjectDir / 'MasterAnalysisFiles'
		self.localSummaryDir = self.localProjectDir / 'Summary'
		self.localAllClipsDir = self.localProjectDir / 'AllClips'
		self.localManualLabelClipsDir = self.localProjectDir / 'MLClips'
		self.localManualLabelFramesDir = self.localProjectDir / 'MLFrames'
		self.localTroubleshootingDir = self.localProjectDir / 'Troubleshooting'
		self.localPaceDir = self.localProjectDir / 'Pace'
		self.localTempDir = self.localProjectDir / 'Temp'

		# Files created by tracker
		self.localFirstFrame = self.localPrepDir / 'FirstDepth.npy'
		self.localLastFrame = self.localPrepDir / 'LastDepth.npy'
		self.localPiRGB = self.localPrepDir / 'PiCameraRGB.jpg'
		self.localDepthRGB = self.localPrepDir / 'DepthRGB.jpg'

		# Files created by prep preparer
		self.localTrayFile = self.localAnalysisDir / 'DepthCrop.txt'
		self.localTransMFile = self.localAnalysisDir / 'TransMFile.npy'
		self.localVideoCropFile = self.localAnalysisDir / 'VideoCrop.npy'
		self.localVideoPointsFile = self.localAnalysisDir / 'VideoPoints.npy'
		self.localPrepSummaryFigure = self.localSummaryDir / 'PrepSummary.pdf'

		# Files created by depth preparer
		self.localSmoothDepthFile = self.localAnalysisDir / 'smoothedDepthData.npy'
		self.localRGBDepthVideo = self.localAnalysisDir / 'DepthRGBVideo.mp4'
		self.localRawDepthFile = self.localTroubleshootingDir / 'rawDepthData.npy'
		self.localInterpDepthFile = self.localTroubleshootingDir / 'interpDepthData.npy'

		# Files created by cluster preparer
		self.localAllLabeledClustersFile = self.localAnalysisDir / 'AllLabeledClusters.csv'

		# Files created by manual labeler preparer
		self.localLabeledFramesFile = self.localAnalysisDir / 'LabeledFrames.csv'
		self.localNewLabeledVideosFile = self.localAnalysisDir / 'NewLabeledVideos.csv'
		self.localNewLabeledClipsDir = self.localProjectDir / 'NewLabeledClips'
		self.localLabeledClipsProjectDir = self.localLabeledClipsDir / projectID

		# Files created by manual labeler preparer
		self.localLabeledFramesFile = self.localAnalysisDir / 'LabeledFrames.csv'

		# Files created by manual labeler preparer

	def createMLData(self, modelID):
		self.vModelID = modelID

		self.local3DModelDir = self.localMLDir / 'VideoModels/' / self.vModelID

		self.localVideoModelFile = self.local3DModelDir / 'model.pth'
		self.localVideoClassesFile = self.local3DModelDir / 'classInd.txt'
		self.localVideoCommandsFile = self.local3DModelDir / 'commands.pkl'
		self.localVideoProjectDictionary = self.local3DModelDir / 'videoToProject.csv'
		self.localVideoLabels = self.local3DModelDir / 'tempVideoPredictions.csv'
		self.localConvertedClipsDir = self.local3DModelDir / 'tempConvertedClips'
		self.localVideoLabelsDir = self.local3DModelDir / 'tempOutputLabels'

	def createAnnotationData(self):
		self.localAnnotationDir = self.localMasterDir / '__AnnotatedData'
		self.localObjectDetectionDir = self.localAnnotationDir / 'BoxedFish'
		self.local3DVideosDir = self.localAnnotationDir / 'LabeledVideos'

		self.localLabeledClipsFile = self.local3DVideosDir / 'ManualLabels.csv'
		self.localLabeledClipsDir = self.local3DVideosDir / 'Clips'
		self.localOrganizedLabeledClipsDir = self.local3DVideosDir / 'OrganizedClips'

		self.localBoxedFishFile = self.localObjectDetectionDir / 'BoxedFish.csv'
		self.localBoxedFishDir = self.localObjectDetectionDir / 'BoxedImages'

	def downloadProjectData(self, dtype):

		if dtype == 'Prep':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localAnalysisDir)
			self.createDirectory(self.localSummaryDir)
			self.downloadData(self.localPrepDir)
			self.downloadData(self.localLogfile)

		elif dtype == 'Depth':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localAnalysisDir)
			self.createDirectory(self.localTroubleshootingDir)
			self.createDirectory(self.localPaceDir)
			self.downloadData(self.localLogfile)
			self.downloadData(self.localFrameDir, tarred = True)

		elif dtype == 'Cluster':
			self.createMLData()
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localAnalysisDir)
			self.createDirectory(self.localTroubleshootingDir)
			self.createDirectory(self.localPaceDir)
			self.createDirectory(self.localTempDir)
			self.createDirectory(self.localAllClipsDir)
			self.createDirectory(self.localManualLabelClipsDir)
			self.createDirectory(self.localManualLabelFramesDir)
			self.createDirectory(self.localManualLabelFramesDir[:-1] + '_pngs')
			self.downloadData(self.localLogfile)
			self.downloadData(self.localVideoDir)

		elif dtype == 'ClusterClassification':
			self.createDirectory(self.localMasterDir)
			self.downloadData(self.localLogfile)
			self.downloadData(self.localAllClipsDir, tarred = True)
			self.downloadData(self.localAnalysisDir)
			self.downloadData(self.localTroubleshootingDir)
			self.downloadData(self.local3DModelDir)

		elif dtype == 'ManualLabelVideos':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localAnalysisDir)
			self.createDirectory(self.localNewLabeledClipsDir)
			self.downloadData(self.localManualLabelClipsDir, tarred_subdirs = True)
			self.downloadData(self.localLabeledClipsFile)

		elif dtype == 'ManualAnnotation':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localAnalysisDir)
			self.downloadData(self.manualLabelFramesDir, tarred = True)
			try:
				self.downloadData(self.localLabeledFramesFile)
			except FileNotFoundError:
				pass

		elif dtype == 'Summary':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localSummaryDir)
			self.downloadData(self.localLogfile)
			self.downloadData(self.localAnalysisDir)
			self.downloadData(self.localPaceDir)

		elif dtype == 'All':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.local3DModelDir)
			self.createDirectory(self.localAnalysisDir)
			self.createDirectory(self.localTroubleshootingDir)
			self.createDirectory(self.localTempDir)
			self.createDirectory(self.localAllClipsDir)
			self.createDirectory(self.localManualLabelClipsDir)
			self.createDirectory(self.localManualLabelFramesDir)
			self.createDirectory(self.localManualLabelFramesDir[:-1] + '_pngs')
			self.createDirectory(self.localSummaryDir)
			self.createDirectory(self.localPaceDir)
			self.downloadData(self.localLogfile)
			self.downloadData(self.localVideoDir)
			self.downloadData(self.localFrameDir, tarred = True)
			self.downloadData(self.local3DModelDir)

		else:
			raise KeyError('Unknown key: ' + dtype)

	def uploadProjectData(self, dtype, videoIndex):
		if dtype == 'Prep':
			self.uploadData(self.localTrayFile)
			self.uploadData(self.localTransMFile)
			self.uploadData(self.localVideoCropFile)
			self.uploadData(self.localVideoPointsFile)
			self.uploadData(self.localPrepSummaryFigure)
		elif dtype == 'Depth':
			self.uploadData(self.localSmoothDepthFile)
			self.uploadData(self.localRGBDepthVideo)
			self.uploadData(self.localRawDepthFile)
			self.uploadData(self.localInterpDepthFile)
			self.uploadData(self.localPaceDir)
		elif dtype == 'Cluster':
			videoObj = self.returnVideoObject(videoIndex)
			self.uploadData(self.localTroubleshootingDir)
			self.uploadData(self.localPaceDir)
			self.uploadData(videoObj.localAllClipsDir, tarred = True)
			self.uploadData(videoObj.localManualLabelClipsDir, tarred = True)
			self.uploadData(videoObj.localManualLabelFramesDir, tarred = True)
		elif dtype == 'Summary':
			self.uploadData(self.localSummaryDir)
		elif dtype == 'ManualAnnotation':
			self.uploadAndMerge(self.localNewLabeledVideosFile, self.localLabeledClipsFile, ID='LID')
			self.uploadAndMerge(self.localNewLabeledClipsDir, self.localLabeledClipsProjectDir, tarred=True)

		else:
			raise KeyError('Unknown key: ' + dtype)

	"""def downloadAnnotationData(self, dtype):
		if dtype == 'LabeledVideos':
			good_count, bad_count = 0,0

			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.local3DVideosDir)
			self.downloadData(self.localLabeledClipsFile)

			# Identify directories that need to be untarred and download them
			labeledProjects = subprocess.run(['rclone', 'lsf', self.localLabeledClipsDir.replace(self.localMasterDir, self.cloudMasterDir)], capture_output = True, encoding = 'utf-8').stdout.split()
			for lp in labeledProjects:
				if '.tar' in lp:
					self.downloadData(self.localLabeledClipsDir + lp.replace('.tar',''), tarred = True)

			# Reorganize data for VideoLoader to automatically download
			dt = pd.read_csv(self.localLabeledClipsFile)
			for row in dt.itertuples():
				dest_dir = self.localOrganizedLabeledClipsDir + row.ManualLabel + '/'
				if not os.path.exists(dest_dir):
					self.createDirectory(dest_dir)
				output = subprocess.run(['mv', self.localLabeledClipsDir + row.ClipName.split('__')[0] + '/' + row.ClipName + '.mp4', dest_dir], capture_output = True, encoding = 'utf-8')
				if output.stderr == '':
					good_count += 1
				else:
					bad_count += 1
			print(str(good_count) + ' labeled videos moved. Missing videos for ' + str(bad_count) + ' total videos.')
			subprocess.call(['rm', '-rf', self.localLabeledClipsDir])

		elif dtype == 'BoxedFish':
			self.createDirectory(self.localMasterDir)
			self.createDirectory(self.localObjectDetectionDir)
			self.downloadData(self.localBoxedFishFile)
			
			boxedProjects = subprocess.run(['rclone', 'lsf', self.localBoxedFishDir.replace(self.localMasterDir, self.cloudMasterDir)], capture_output = True, encoding = 'utf-8').stdout.split()
			for bp in boxedProjects:
				if '.tar' in bp:
					self.downloadData(self.localBoxedFishDir + bp.replace('.tar',''), tarred = True)
		else:
			raise KeyError('Unknown key: ' + dtype)"""

	def returnVideoObject(self, index):
		from Modules.LogParser import LogParser as LP
		self._createParameters()

		self.downloadData(self.localLogfile)
		self.lp = LP(self.localLogfile)
		videoObj = self.lp.movies[index]
		videoObj.localVideoFile = self.localProjectDir / videoObj.mp4_file
		videoObj.localHMMFile = self.localTroubleshootingDir / videoObj.baseName + '.hmm'
		videoObj.localRawCoordsFile = self.localTroubleshootingDir / videoObj.baseName + '_rawCoords.npy'
		videoObj.localLabeledCoordsFile = self.localTroubleshootingDir / videoObj.baseName + '_labeledCoords.npy'
		videoObj.localLabeledClustersFile = self.localTroubleshootingDir / videoObj.baseName + '_labeledClusters.csv'
		videoObj.localAllClipsDir = self.localAllClipsDir / videoObj.baseName
		videoObj.localManualLabelClipsDir = self.localManualLabelClipsDir / videoObj.baseName + '/'
		videoObj.localManualLabelFramesDir = self.localManualLabelFramesDir / videoObj.baseName + '/'
		videoObj.localAllClipsPrefix = self.localAllClipsDir / self.lp.projectID + '_' + videoObj.baseName
		videoObj.localManualLabelClipsPrefix = self.localManualLabelClipsDir / self.lp.projectID + '_' + videoObj.baseName
		videoObj.localIntensityFile = self.localSummaryDir / videoObj.baseName + '_intensity.pdf'
		videoObj.localTempDir = self.localTempDir / videoObj.baseName
		videoObj.nManualLabelClips = int(self.nManualLabelClips/len(self.lp.movies))
		videoObj.nManualLabelFrames = int(self.nManualLabelFrames/len(self.lp.movies))
		
		self.createDirectory(videoObj.localTempDir)

		return videoObj

	def _createParameters(self):

		# Depth related parameters
		self.hourlyDepthThreshold = 0.2  # cm
		self.dailyDepthThreshold = 0.4  # cm
		self.totalDepthThreshold = 1.0  # cm

		# Cluster related parameters
		self.hourlyClusterThreshold = 0.6  # events/cm^2
		self.dailyClusterThreshold = 1.2  # events/cm^2
		self.totalClusterThreshold = 3.0  # events/cm^2

		# Parameters related to both depth and cluster analysis
		self.hourlyMinPixels = 1000
		self.dailyMinPixels = 1000
		self.totalMinPixels = 1000
		self.pixelLength = 0.1030168618 # cm / pixel
		self.bowerIndexFraction = 0.1

		# Video related parameters
		self.lightsOnTime = 8
		self.lightsOffTime = 18

		# DB Scan related parameters
		self.minMagnitude = 0
		self.treeR = 22 
		self.leafNum = 190 
		self.neighborR = 22
		self.timeScale = 10
		self.eps = 18
		self.minPts = 90 
		self.delta = 1.0 # Batches to calculate clusters

		# Clip creation parameters
		self.nManualLabelClips = 1200
		self.delta_xy = 100
		self.delta_t = 60
		self.smallLimit = 500

		# Manual Label Frame 
		self.nManualLabelFrames = 500

	def _identifyPiDirectory(self):
		writableDirs = []
		try:
			possibleDirs = os.listdir('/media/pi')
		except FileNotFoundError:
			return

		for d in possibleDirs:

			try:
				with open('/media/pi/' + d + '/temp.txt', 'w') as f:
					print('Test', file = f)
				with open('/media/pi/' + d + '/temp.txt', 'r') as f:
					for line in f:
						if 'Test' in line:
							writableDirs.append(d)
			except:
				pass
			try:
				os.remove('/media/pi/' + d + '/temp.txt')
			except FileNotFoundError:
				continue
		
		if len(writableDirs) == 1:
			self.localMasterDir = '/media/pi/' + d + '/CichlidAnalyzer/'
			self.system = 'pi'
		elif len(writableDirs) == 0:
			raise Exception('No writable drives in /media/pi/')
		else:
			raise Exception('Multiple writable drives in /media/pi/. Options are: ' + str(writableDirs))

	def createDirectory(self, directory):
		if not os.path.exists(directory):
			os.makedirs(directory)

	def downloadData(self, local_data, tarred = False, tarred_subdirs = False):
		local_data = Path(local_data).as_posix()

		relative_name = local_data.rstrip('/').split('/')[-1] + '.tar' if tarred else local_data.rstrip('/').split('/')[-1]
		local_path = local_data.split(local_data.rstrip('/').split('/')[-1])[0]
		cloud_path = local_path.replace(self.localMasterDir.as_posix(), self.cloudMasterDir)

		cloud_objects = subprocess.run(['rclone', 'lsf', cloud_path], capture_output = True, encoding = 'utf-8').stdout.split()

		if relative_name + '/' in cloud_objects: #directory
			output = subprocess.run(['rclone', 'copy', cloud_path + relative_name, local_path + relative_name], capture_output = True, encoding = 'utf-8')
		elif relative_name in cloud_objects: #file
			output = subprocess.run(['rclone', 'copy', cloud_path + relative_name, local_path], capture_output = True, encoding = 'utf-8')
		else:
			raise FileNotFoundError('Cant find file for download: ' + cloud_path + relative_name)

		if not os.path.exists(local_path + relative_name):
			raise FileNotFoundError('Error downloading: ' + local_path + relative_name)

		if tarred:
			# Untar directory
			output = subprocess.run(['tar', '-xvf', local_path + relative_name, '-C', local_path], capture_output = True, encoding = 'utf-8')
			output = subprocess.run(['rm', '-f', local_path + relative_name], capture_output = True, encoding = 'utf-8')

		if tarred_subdirs:
			for d in [x for x in os.listdir(local_data) if '.tar' in x]:
				output = subprocess.run(['tar', '-xvf', local_data + d, '-C', local_data, '--strip-components', '1'], capture_output = True, encoding = 'utf-8')
				os.remove(local_data + d)

	def uploadData(self, local_data, tarred = False):
		local_data = Path(local_data).as_posix()

		relative_name = local_data.rstrip('/').split('/')[-1]
		local_path = local_data.split(relative_name)[0]
		cloud_path = local_path.replace(self.localMasterDir.as_posix(), self.cloudMasterDir)

		if tarred:
			output = subprocess.run(['tar', '-cvf', local_path + relative_name + '.tar', '-C', local_path, relative_name], capture_output = True, encoding = 'utf-8')
			if output.returncode != 0:
				print(output.stderr)
				raise Exception('Error in tarring ' + local_data)
			relative_name += '.tar'

		if os.path.isdir(local_path + relative_name):
			output = subprocess.run(['rclone', 'copy', local_path + relative_name, cloud_path + relative_name], capture_output = True, encoding = 'utf-8')
			#subprocess.run(['rclone', 'check', local_path + relative_name, cloud_path + relative_name], check = True)

		elif os.path.isfile(local_path + relative_name):
			print(['rclone', 'copy', local_path + relative_name, cloud_path])
			output = subprocess.run(['rclone', 'copy', local_path + relative_name, cloud_path], capture_output = True, encoding = 'utf-8')
			output = subprocess.run(['rclone', 'check', local_path + relative_name, cloud_path], check = True, capture_output = True, encoding = 'utf-8')
		else:
			raise Exception(local_data + ' does not exist for upload')

		if output.returncode != 0:
			pdb.set_trace()
			raise Exception('Error in uploading file: ' + output.stderr)

	def uploadAndMerge(self, local_data, master_file, tarred = False, ID = False):
		if os.path.isfile(local_data):
			#We are merging two crv files
			self.downloadData(master_file)

			if ID:
				old_dt = pd.read_csv(master_file, index_col = ID)
				new_dt = pd.read_csv(local_data, index_col = ID)
				old_dt = old_dt.append(new_dt)
				old_dt.index.name = ID
			else:
				old_dt = pd.read_csv(master_file)
				new_dt = pd.read_csv(local_data)
				old_dt = old_dt.append(new_dt)

			old_dt.to_csv(master_file, sep = ',')
			self.uploadData(master_file)
		else:
			#We are merging two tarred directories
			try:
				self.downloadData(master_file, tarred = True)
			except FileNotFoundError:
				self.createDirectory(master_file)
			for nfile in os.listdir(local_data):
				subprocess.run(['mv', local_data + nfile, master_file])
			self.uploadData(master_file, tarred = True)

