# Cellpose Trackmate Script
'''
Script to automate running trackmate-cellpose on a folder of .tif images (specified with a GUI) for a list of specified object PIXEL size.
Will produce individual folders for each image each containing the image and separate trackmate .xml files for every object PIXEL size
Need to have cellpose installed on your computer, and point trackmate to it.  You can set the path to cellpose under the "configure detector" section.  As Cellpose3 (as opposed to cellpose sam) uses an initial diameter as a starting point, we have this set to use a list of starting diameters, so the user can segment with multiple diameters at the same time, and judge later what works
'''

import sys
import os
import glob
import shutil

from ij import IJ
from ij import WindowManager
 
from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.util import LogRecorder
from fiji.plugin.trackmate.util import TMUtils
from fiji.plugin.trackmate.io import TmXmlWriter
from fiji.plugin.trackmate.cellpose import CellposeDetectorFactory
from fiji.plugin.trackmate.cellpose.CellposeSettings import PretrainedModel
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.action import LabelImgExporter
from fiji.plugin.trackmate.action.LabelImgExporter.LabelIdPainting import LABEL_IS_TRACK_ID


from javax.swing import (JFileChooser, JFrame, JPanel, JLabel)
from java.awt import BorderLayout, FlowLayout
from java.io import File
from java.lang import Double

class DropDown(JFrame):
	def __init__(self):
		super(DropDown, self).__init__()
		self.initUI()

	def initUI(self):
		self.panel = JPanel()
		self.panel.setLayout(BorderLayout())

		chosenFile = JFileChooser()

		chosenFile.setDialogTitle('Select Root Directory')
		chosenFile.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)

		ret = chosenFile.showOpenDialog(self.panel)

		if ret == JFileChooser.APPROVE_OPTION:
			if chosenFile.getSelectedFile().isDirectory():
				self.file_name = str(chosenFile.getSelectedFile())

	def get_file_name(self):
		return self.file_name
		
# GUI to find root directory with all images to be analysed
GUI = DropDown()
root_dir = GUI.get_file_name()
#print("Looking in " + root_dir " for tiff images")

filenames = [os.path.basename(file_path) for file_path in glob.glob(root_dir + '/*.tif')]

# List of pixel sizes for cellpose detection
PixelSizes = [10., 20., 15.]

for filename in filenames: 
	#open image
	
	full_filepath = root_dir + '/' + filename
	imp = IJ.openImage(full_filepath)
	
	# check if file has z-slices
	num_slices = imp.getNSlices()
	print(str(filename) + " has " + str(num_slices) + " z slices")
	
	# if 3D convert to 2D+t
	if num_slices > 1:
		print("Converting 3D image to 2D+t and saving")
		IJ.run(imp, "Re-order Hyperstack ...", "channels=[Channels (c)] slices=[Frames (t)] frames=[Slices (z)]");
		imp.removeScale();
		IJ.saveAs("tiff", full_filepath);
	
	# make new directory to store all files
	new_dir_path = root_dir + '/' + os.path.splitext(filename)[0]
	
	# if directory already exists, remove and make new
	if os.path.exists(new_dir_path):
		print(new_dir_path + " already exists, deleting")
		shutil.rmtree(new_dir_path)
		
	os.mkdir(new_dir_path)
	
	print('Directory ' + new_dir_path + ' created')
	
	for PixelSize in PixelSizes:
		# full_filepath = root_dir + '/' + filename
		imp = IJ.openImage(full_filepath)
		
		print('Detecting ' + filename + ' at ' + str(PixelSize))
		
		# Logger -> content will be saved in the XML file.
		logger = LogRecorder( Logger.VOID_LOGGER )
		
		settings = Settings(imp)
		
		settings.detectorFactory = CellposeDetectorFactory()
		
		# Configure detector
		settings.detectorSettings = {
		    'TARGET_CHANNEL' : 0,
		    'OPTIONAL_CHANNEL_2' : 0,
		    'CELLPOSE_PYTHON_FILEPATH' : '/nemo/stp/lm/working/daov/.conda/envs/cellpose_attempt/bin/python',
		    'CELLPOSE_MODEL' : PretrainedModel.CYTO2,
		    'CELLPOSE_MODEL_FILEPATH' : '/nemo/stp/lm/working/daov/.cellpose/models',
		    'CELL_DIAMETER' : PixelSize,
		    'USE_GPU' : True,
		    'SIMPLIFY_CONTOURS' : True,
		}
		
		# Configure tracker - default settings then change bits
		settings.trackerFactory = SparseLAPTrackerFactory()
		settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
		settings.trackerSettings['LINKING_MAX_DISTANCE'] = 3.0
		settings.trackerSettings['MAX_FRAME_GAP'] = 2
		settings.trackerSettings['ALLOW_GAP_CLOSING'] = True
		settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 3.0
		settings.trackerSettings['ALTERNATIVE_LINKING_COST_FACTOR'] = 1.05
		settings.trackerSettings['CUTOFF_PERCENTILE'] = 0.9

		# Add ALL feature analysers known to TrackMate
		# Will yield numerical features for results e.g speed, mean intensity, etc.
		settings.addAllAnalyzers()
		
		trackmate = TrackMate(settings)
		trackmate.computeSpotFeatures( True )
		trackmate.computeTrackFeatures( True )
		model = trackmate.getModel()
		model.setLogger( logger )
		
		ok = trackmate.checkInput()
		if not ok:
		    print( str( trackmate.getErrorMessage() ) )
		
		
		ok = trackmate.process()
		if not ok:
		    print( str( trackmate.getErrorMessage() ) )

		# Export tracks to xml file in new directory
		XmlFilename = os.path.splitext(filename)[0] + '_' + str(int(PixelSize)) +'_pixels.xml'
		saveFile = File(new_dir_path, XmlFilename)
		
		writer = TmXmlWriter( saveFile, logger )
		writer.appendLog( logger.toString() )
		writer.appendModel( trackmate.getModel())
		writer.appendSettings( trackmate.getSettings() )
		writer.writeToFile();
		
		lblImg = LabelImgExporter()
		lblImg = LabelImgExporter.createLabelImagePlus(trackmate, False,  True, LABEL_IS_TRACK_ID).show()
		imp2 = IJ.getImage()
		new_filepath = new_dir_path + '/' + filename
		segmentation_filename = os.path.splitext(filename)[0] + '_' + str(int(PixelSize)) +'_pixels_segmentation.tif'
		IJ.saveAs(imp2, "Tiff", new_filepath+segmentation_filename)
		imp2.close() #close the segmentation map
		
		print( "Results saved to: " + saveFile.toString() + '\n' );
		
		#https://forum.image.sc/t/trackmate-labelimgexporter-scripting-v7-11-1/91071
		#https://github.com/trackmate-sc/TrackMate/commit/625a54a70d06e1d4b734a924feef4c7d9b4eab10
		#https://forum.image.sc/t/scripting-id-assignment-for-labels-in-trackmate-7-13-label-image-exporter/99512/3
	# finish processing image
	# finally move image to new directory
	new_filepath = new_dir_path + '/' + filename
	#os.rename(full_filepath, new_filepath)
	shutil.copy(full_filepath, new_filepath)
	imp.close()
