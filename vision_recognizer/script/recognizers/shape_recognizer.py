#!/usr/bin/env python

# Future imports
from __future__ import print_function

# Regular imports
import sys
import numpy as np
import cv2
import os
import signal

# Scikit learn

from sklearn.preprocessing import scale
from sklearn.externals import joblib
from sklearn.svm import SVC

# ROS imports
import rospy
from sensor_msgs.msg import Image
from ras_vision_recognizer.msg import Rect
from cv_bridge import CvBridge
from std_msgs.msg import UInt8


class ShapeRecognizer:

    def __init__(self):

        signal.signal(signal.SIGINT, signal_callback)

        self.node_name = 'shape_recognizer'

        # cv2.namedWindow('original', cv2.WINDOW_NORMAL)
        # cv2.createTrackbar('blur', 'original', 0, 20, self.cb)

        cv2.namedWindow('equalized', cv2.WINDOW_NORMAL)
        # cv2.createTrackbar('lower', 'canny', 0, 255, self.cb)
        # cv2.createTrackbar('upper', 'canny', 0, 255, self.cb)

        self.bridge = CvBridge()

        rospy.init_node(self.node_name, anonymous=True)

        self.image = None

        self.count = 0

        self.directory = '/home/fabian/images/'

        self.clf = joblib.load('/home/fabian/catkin_ws/src/ras_vision/ras_vision_svm/svm.pkl')

        self.subscriber = rospy.Subscriber('/camera/rgb/image_raw', Image, self.color_callback, queue_size=1)
        self.subscriber = rospy.Subscriber('/vision/object_rect', Rect, self.object_callback, queue_size=1)

        self.publisher = rospy.Publisher('/object/shape', UInt8, queue_size=1)

    def cb(self, x):
        pass

    def color_callback(self, data):

        self.image = self.bridge.imgmsg_to_cv2(data, 'bgr8')

    def object_callback(self, d):

        # Return if no image available
        if self.image is None:
            return

        # Crop the object
        image = self.image[d.y:d.y + d.height, d.x:d.x + d.width]

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image = cv2.equalizeHist(image)

        image = cv2.resize(image, (30, 30))

        cv2.imshow('equalized', image)

        # image = cv2.blur(image, (3, 3))

        # cv2.imshow('original', image)

        # mask = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 2)

        # opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, (5, 5))

        # resized = cv2.resize(opening, (30, 30))

        # cv2.imshow('canny', resized)

        self.classify(image)

        key = cv2.waitKey(1)

        if key == 10:
            filename = self.directory + 'image' + str(self.count + 1) + '.jpg' 
            cv2.imwrite(filename, image)
            print('Captured image: ' + filename)
            self.count += 1

        if key == 27: # ESC key pressed
            shutdown()

    def classify(self, image):

        data = np.array(image, dtype=np.float32)
        flattened = data.flatten()
        x = scale(flattened)
        #predition = self.clf.predict(x)

        prob_cube, prob_sphere = self.clf.predict_proba(x)[0]

        if prob_cube > 0.6:
            print('Shape: cube (' + str(prob_cube) + ')' , end='\r')
        elif prob_sphere > 0.6:
            print('Shape: sphr (' + str(prob_sphere) + ')', end='\r')
        sys.stdout.flush()

        #msg = UInt8()
        #msg.data = int(predition)
        #self.publisher.publish(msg)

        #shape = 'cube' if predition == 0 else 'sphr'

        #print('Shape: ' + shape, end='\r')
        #


def signal_callback(signal, frame):
    shutdown()

def shutdown():
    sys.stdout.flush()
    print()
    print('Quitting...')
    rospy.signal_shutdown('Quitting...')
    cv2.destroyAllWindows()

def main():
    print('Running... Press CTRL-C to quit.')
    ShapeRecognizer()
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print('Quitting')
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
