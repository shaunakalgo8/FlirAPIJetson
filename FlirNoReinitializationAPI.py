import time
import os
import PySpin
import sys
import numpy
from flask import Flask, request, jsonify
import json
import pickle
import logging
from datetime import datetime

app = Flask(__name__)

logger = logging.getLogger('FLIRAPI')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

global cam
cam_list = []
global system

def init_camera():
    try:
        global cam
        global cam_list
        global system

        system = PySpin.System.GetInstance()

        # Get current library version
        version = system.GetLibraryVersion()
        #print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

        # Retrieve list of cameras from the system
        cam_list = system.GetCameras()

        num_cameras = cam_list.GetSize()

        #print('Number of cameras detected: %d' % num_cameras)
        logger.info('Process Starting')
        # Finish if there are no cameras
        if num_cameras == 0:

            # Clear camera list before releasing system
            cam_list.Clear()

            # Release system instance
            system.ReleaseInstance()

            print('Not enough cameras!')
            input('Done! Press Enter to exit...')
        print('Error break')
        
        cam_list[0]

        print(cam_list[0])

        
        cam = cam_list[0]

        nodemap_tldevice = cam.GetTLDeviceNodeMap()

        # Initialize camera
        cam.Init()

        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()

        sNodemap = cam.GetTLStreamNodeMap()
        # Change bufferhandling mode to NewestOnly
        node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))

        node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
        node_pixel_format_mono16 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono16'))
        pixel_format_mono16 = node_pixel_format_mono16.GetValue()
        node_pixel_format.SetIntValue(pixel_format_mono16)


        # This section is to be activated only to set the streaming mode to TemperatureLinear10mK
        node_IRFormat = PySpin.CEnumerationPtr(nodemap.GetNode('IRFormat'))
        node_temp_linear_high = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('TemperatureLinear10mK'))
        node_temp_high = node_temp_linear_high.GetValue()
        node_IRFormat.SetIntValue(node_temp_high)

        #if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
            #print('Unable to set stream buffer handling mode.. Aborting...')

        # Retrieve entry node from enumeration node
        node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
        #if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
            #print('Unable to set stream buffer handling mode.. Aborting...')

        # Retrieve integer value from entry node
        node_newestonly_mode = node_newestonly.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

        #print('*** IMAGE ACQUISITION ***\n')

        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        #if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            #print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        #if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                #node_acquisition_mode_continuous):
            #print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')

        # Retrieve integer value from entry node
        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        #print('Acquisition mode set to continuous...')
    except Exception as e:
        print(e)
        return("Error")
        
def getTemp(xEyeRight,yEyeRight,rightEyeRight,bottomEyeRight,xEyeLeft,yEyeLeft,rightEyeLeft,bottomEyeLeft,xNose,yNose,rightNose,bottomNose,xforehead,yforehead,wforehead,hforehead,xface,yface,rightface,bottomface):
#def getTemp(xEyeRight,yEyeRight,rightEyeRight,bottomEyeRight,xEyeLeft,yEyeLeft,rightEyeLeft,bottomEyeLeft):
# Retrieve singleton reference to system object
    try:
        #  Begin acquiring images
        global cam
        global cam_list
        global system

        print('---------------Starting Get Temp---------------')
        print('Camera getTemp: ',cam)
        print('Camera List getTemp: ',cam_list)
        print('System getTemp: ',system)
        cam.BeginAcquisition()

        print('Acquiring images...')

        #device_serial_number = ''
        #node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
        #if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
        #    device_serial_number = node_device_serial_number.GetValue()
            #print('Device serial number retrieved as %s...' % device_serial_number)

        continue_recording = True
        count_frame = 0
        temp_arr = []
        image_incomplete_flag = True
        data_flag = 0

        while image_incomplete_flag and data_flag<2:
            try:
                print('1')
                image_result = cam.GetNextImage()

                #  Ensure image completion
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                    logger.info('Incomplete Image from Camera')

                else:                    

                    # Getting the image data as a numpy array
                    image_data = image_result.GetNDArray()


                    # Transforming the data array into a temperature array, if streaming mode is set to TemperatueLinear10mK
                    image_Temp_Celsius_high=(image_data*0.01) - 273.15
                    #image_Temp_Celsius_high=(image_data*0.01) - 274.15
                    count_frame = count_frame+1
                    temp_arr = image_Temp_Celsius_high.copy()
                    #print('Frame Number:',count_frame)
                    print("max temp: ",image_Temp_Celsius_high.max())
                    #print("min temp: ",image_Temp_Celsius_high.min())
                    #print(image_Temp_Celsius_high)
                    data_flag = data_flag + 1

                    if data_flag==2:
                        image_incomplete_flag =  False

                image_result.Release()
            except Exception as e:
                print(e)

        print('1')
        cam.EndAcquisition()
        faceTempEyeRight = round(numpy.max(temp_arr[yEyeRight:bottomEyeRight,xEyeRight:rightEyeRight]),2)
        logger.info('FaceTempEyeRight: {}'.format(faceTempEyeRight))
        faceTempEyeLeft = round(numpy.max(temp_arr[yEyeLeft:bottomEyeLeft,xEyeLeft:rightEyeLeft]),2)
        logger.info('faceTempEyeLeft: {}'.format(faceTempEyeLeft))
        faceTempNose = round(numpy.max(temp_arr[yNose:bottomNose,xNose:rightNose]),2)
        logger.info('faceTempNose: {}'.format(faceTempNose))
        faceTempForehead = round(numpy.max(temp_arr[yforehead:hforehead,xforehead:wforehead]),2)
        logger.info('faceTempForehead: {}'.format(faceTempForehead))
        faceTemp = round(numpy.max(temp_arr[yface:bottomface,xface:rightface]),2)
        logger.info('faceTemp: {}'.format(faceTemp))
        json_strEyeRight = json.dumps(faceTempEyeRight)
        json_strEyeLeft = json.dumps(faceTempEyeLeft)
        json_strNose = json.dumps(faceTempNose)

        #tuppleTemp = ("EyeRight: {}".format(json_strEyeRight),"EyeLeft: {}".format(json_strEyeLeft),"Nose: {}".format(json_strNose))
        abcdef = {"EyeRight":json_strEyeRight,"EyeLeft":json_strEyeLeft,"Nose":json_strNose}
        return abcdef
    except Exception as e:
        print(e)
        return("Error")

@app.route('/', methods = ['GET', 'POST'])
def index():
    try:
        start = time.time()
        xEyeRight = int(request.args.get('xEyeRight'))
        yEyeRight = int(request.args.get('yEyeRight'))
        rightEyeRight = int(request.args.get('rightEyeRight'))
        bottomEyeRight = int(request.args.get('bottomEyeRight'))

        xEyeLeft = int(request.args.get('xEyeLeft'))
        yEyeLeft = int(request.args.get('yEyeLeft'))
        rightEyeLeft = int(request.args.get('rightEyeLeft'))
        bottomEyeLeft = int(request.args.get('bottomEyeLeft'))

        xNose = int(request.args.get('xNose'))
        yNose = int(request.args.get('yNose'))
        rightNose = int(request.args.get('rightNose'))
        bottomNose = int(request.args.get('bottomNose'))

        xforehead = int(request.args.get('xforehead'))
        yforehead = int(request.args.get('yforehead'))
        wforehead = int(request.args.get('wforehead'))
        hforehead = int(request.args.get('hforehead'))

        xface = int(request.args.get('xface'))
        yface = int(request.args.get('yface'))
        rightface = int(request.args.get('rightface'))
        bottomface = int(request.args.get('bottomface'))
        
        print(xEyeRight,yEyeRight,rightEyeRight,bottomEyeRight,xEyeLeft,yEyeLeft,rightEyeLeft,bottomEyeLeft,xNose,yNose,rightNose,bottomNose,xforehead,yforehead,wforehead,hforehead,xface,yface,rightface,bottomface)
        response = getTemp(xEyeRight,yEyeRight,rightEyeRight,bottomEyeRight,xEyeLeft,yEyeLeft,rightEyeLeft,bottomEyeLeft,xNose,yNose,rightNose,bottomNose,xforehead,yforehead,wforehead,hforehead,xface,yface,rightface,bottomface)
        
        print(response)  
        
        Ttime = time.time() - start
        logger.info('Total Time: {}'.format(Ttime))
        return jsonify(response)
    except:
        return "Error Encountered"

if __name__ == '__main__':    
    init_camera()
    app.run(host='0.0.0.0', port = 7006)
