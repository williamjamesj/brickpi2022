#https://www.hackster.io/ruchir1674/video-streaming-on-flask-server-using-rpi-ef3d75-----------------------#

import time
import io
import threading
import picamera
import cv2
import numpy
import logging

class Camera(object):

    def __init__(self):
        self.frame = None  # current frame is stored here by background thread
        self.thread_running = True
        self.thread = threading.Thread(target=self.__thread)
        self.thread.start()
        self.logger=logging.getLogger()
        return

    def log(self, message):
        self.logger.info(message)
        return

    def get_frame(self):
        return self.frame

    def exit_thread(self):
        self.thread_running == False
        return

    def __thread(self):
        with picamera.PiCamera() as camera:
            # camera setup
            camera.resolution = (320, 240)
            camera.hflip = True
            camera.vflip = True

            # let camera warm up
            camera.start_preview()
            time.sleep(2)
            self.log("CAMERA INTERFACE: Started Camera Thread")

            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                if self.thread_running == False:
                    self.log("CAMERA INTERFACE: Exiting Camera Thread")
                    break

                # store frame
                stream.seek(0)
                self.frame = stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

        self.thread_running = False
        self.thread = None
        return
    
    #detect if there is a colour in the image
    def get_camera_colour(self):
        img = cv2.imdecode(numpy.fromstring(self.frame, dtype=numpy.uint8), 1)
        self.log(img)
        # set red range
        lowcolor = (50,50,150)
        highcolor = (128,128,255)

        # threshold
        thresh = cv2.inRange(img, lowcolor, highcolor)

        cv2.imwrite("threshold.jpg", thresh)

        count = numpy.sum(numpy.nonzero(thresh))
        self.log("RED PIXELS: " + str(count))
        if count > 300: #more than quarter of total pixels are red
            return "red"
        return "no colour"