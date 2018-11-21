#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64

def extractFrames(fileName, outputBuffer):
    # Initialize frame count 
    count = 0
    
    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success,image = vidcap.read()
    
    print("Reading frame {} {} ".format(count, success))
    while success:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        #encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)

        # add the frame to the buffer
        emptyCountExt.acquire()
        outputBuffer.put(jpgAsText)
        fillCountExt.release()
       
        success,image = vidcap.read()
        print('Reading frame {} {}'.format(count, success))
        count += 1

    emptyCountExt.acquire()
    outputBuffer.put(True)
    fillCountExt.release()
    print("Frame extraction complete")
    return

def convertFrames(inputBuffer, outputBuffer):
    count = 0
    while True:
        # get the next frame
        fillCountExt.acquire()
        frameAsText = inputBuffer.get()
        emptyCountExt.release()

        if frameAsText == True:
            break

        # decode the frame 
        jpgRawImage = base64.b64decode(frameAsText)

        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)

        # convert to an image
        img = cv2.imdecode( jpgImage ,cv2.IMREAD_UNCHANGED)

        # set image to grayscale
        grayscaleFrame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # convert image to jpg
        success, jpgImage = cv2.imencode('.jpg', grayscaleFrame)

        # encode the frame
        jpgAsText = base64.b64encode(jpgImage)
        
        # add the frame to the buffer
        emptyCountCnv.acquire()
        outputBuffer.put(jpgAsText)
        fillCountCnv.release()

        print("Converting frame {}".format(count))  

        count += 1
    emptyCountCnv.acquire()
    outputBuffer.put(True)
    fillCountCnv.release()
    print("Frame conversion complete")


def displayFrames(inputBuffer):
    # initialize frame count
    count = 0
    while True:
        # get the next frame
        fillCountCnv.acquire()
        frameAsText = inputBuffer.get()
        emptyCountCnv.release()

        if frameAsText == True:
            break

        # decode the frame 
        jpgRawImage = base64.b64decode(frameAsText)

        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)
        
        # get a jpg encoded frame
        img = cv2.imdecode( jpgImage ,cv2.IMREAD_UNCHANGED)

        print("Displaying frame {}".format(count))        

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow("Video", img)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break

        count += 1

    print("Finished displaying all frames")
    # cleanup the windows
    cv2.destroyAllWindows()

class Queue:
    def __init__(self, initArray = []):
        self.a = []
        self.a = [x for x in initArray]
    def put(self, item):
        self.a.append(item)
    def get(self):
        a = self.a
        item = a[0]
        del a[0]
        return item
    def __repr__(self):
        return "Q(%s)" % self.a


# filename of clip to load
filename = 'clip.mp4'
BUFF_SIZE = 10

fillCountExt = threading.Semaphore(0)
emptyCountExt = threading.Semaphore(BUFF_SIZE)
fillCountCnv = threading.Semaphore(0)
emptyCountCnv = threading.Semaphore(BUFF_SIZE)

# shared queue  
extractionQueue = Queue()
conversionQueue = Queue()

# extract the frames
extract = threading.Thread(target=extractFrames, args=(filename, extractionQueue))

# convert the frames
convert = threading.Thread(target=convertFrames, args=(extractionQueue, conversionQueue))

# display the frames
display = threading.Thread(target=displayFrames, args=(conversionQueue,))

extract.start()
convert.start()
display.start()