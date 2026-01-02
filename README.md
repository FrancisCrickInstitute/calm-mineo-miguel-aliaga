# calm-mineo-miguel-aliaga
Code for image analysis for "The sex and reproductive plasticity of intestinal muscles instruct gut size"

There are three files here that were used for the data analysis.  
Trackmate_Cellpose_GUI_No_Human.py -- Written mostly by Vanessa Dao, this file is the workhorse of the segmentation. It allows you to choose a CellPose model and run the model on your data without human intervnetion. In this manner, it can be run on many images (it is not paraellilised, it will run one after another) to do segmentations.  As Cellpose 3 required a diameter input to run, the script is configured so that you can enter a list of diameters you would like to use as segmentation basis.  To run this code you MUST have Cellpose installed on your system, as well as Fiji with trackmate. Cellpose can be found at https://www.cellpose.org and fiji trackmate can be found at https://imagej.net/plugins/trackmate/.  We pre-configured this code to use reasonable filters on spots and tracks, but these can be changed.

To use: set the list of pixel sizes for diameter: (seen in the code as below, note: you have to write it as 10. not 10)
# List of pixel sizes for cellpose detection
PixelSizes = [10., 20., 15.]

Point trackmate to your cellpose installation:
under configure detector, change the CELLPOSE_PYTHON_FILEPATH, CELLPOSE_MODEL_FILEPATH and CELLPOSE_MODEL, to the appropriate places for your installation. Here you can also change the model for the appropriate model for your image set

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

The other files here: Ale_Data_Analaysis_Step_1.ipynb and Ale_Data_Analaysis_Step_2.ipynb are jupyter notebooks that are fairly self explanatory
Step 1 takes the segmentation image file, and using sci-kit image and region props, removes the segmentations touching the border, and for each segmentation measures the volume and centroid position of the object. This is then exported to a csv file which is used in step 2

Step 2 imports the csv file, and then rescales the volume to SI units from voxels, using the settings from the microscope. NOTE! in our settings, we had Z=1, so there wasn't much complicated math converting from voxels to volumes, this may not be the case in all situations. 
Step 2 then continues to filter out small objects, which were likely foreign matter in the images, and the largest 2% of the segmentations, which were likely joined up nuclei that were hard to segment.

Note: In all images, the only section of the images that were segmented were first identified by an expert biologist, and and ROI was drawn around them in FIJI. 

