#!/usr/bin/env python

# Regular imports
import sys
import numpy as np
import cv2

# ROS imports
import rospy
from sensor_msgs.msg import Image
from ras_vision_recognizer.msg import Rect
from cv_bridge import CvBridge


class ColorRecognizer:

    def __init__(self):

        self.node_name = 'color_recognizer'

        rospy.init_node(self.node_name, anonymous=True)

        self.subscriber = rospy.Subscriber('/camera/rgb/image_raw', Image, self.color_callback, queue_size=1)
        self.subscriber = rospy.Subscriber('vision/object_rect', Rect, self.object_callback, queue_size=1)

        self.bridge = CvBridge()

        cv2.namedWindow('thresh', cv2.WINDOW_NORMAL)
        cv2.createTrackbar('hue_min', 'thresh', 0, 179, self.cb)
        cv2.createTrackbar('hue_max', 'thresh', 179, 179, self.cb)
        cv2.createTrackbar('sat_min', 'thresh', 130, 255, self.cb)
        cv2.createTrackbar('sat_max', 'thresh', 255, 255, self.cb)
        cv2.createTrackbar('val_max', 'thresh', 255, 255, self.cb)

        cv2.namedWindow('edges', cv2.WINDOW_NORMAL)
        cv2.createTrackbar('blur', 'edges', 0, 30, self.cb)
        cv2.createTrackbar('kernel', 'edges', 0, 30, self.cb)

        self.image = None

    def cb(self, x):
        pass

    def object_callback(self, data):

        # Return if no image available
        if self.image is None:
            return

        # Crop the object
        image = self.image[data.y:data.y + data.height, data.x:data.x + data.width]

        cv2.imshow('object', image)

        thresh, mask = self.color_threshold(image)
        cv2.imshow('thresh', thresh)

        color, prob = self.classify_color(thresh)

        print(color + ' (' + str(prob) + ')')

        shape = self.classify_shape(image)

        cv2.waitKey(1)

    def classify_shape(self, image):

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        blur = cv2.getTrackbarPos('blur', 'edges')

        if blur > 0:
            gray = cv2.blur(gray, (blur, blur))

        kernel = cv2.getTrackbarPos('kernel', 'edges')

        if kernel > 2 and kernel % 2 == 1:
            mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, kernel, 2)
        else:
            mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 2)    

        

        #threshold1 = cv2.getTrackbarPos('threshold1', 'edges')
        #threshold2 = cv2.getTrackbarPos('threshold2', 'edges')

        #edges = cv2.Canny(gray, threshold1, threshold2)

        #contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #cv2.drawContours(gray, contours, -1, (0, 0, 0))

        # for contour in contours:

        #     approx = cv2.approxPolyDP(contour, 0.1 * cv2.arcLength(contour, True), True)

        #     print(len(approx))

        # orb = cv2.ORB()

        # kp = orb.detect(image, None)

        # kp, des = orb.compute(image, kp)

        # img = cv2.drawKeypoints(image, kp, color=(0, 255, 0), flags=0)

        cv2.imshow('edges', mask)

    def classify_color(self, object_image):

        #cv2.imshow('object', object_image)

        hsv_image = cv2.cvtColor(object_image, cv2.COLOR_BGR2HSV)

        hist = cv2.calcHist([hsv_image], [0], None, [180], [1, 179])

        total = float(np.sum(hist))
        orange = np.sum(hist[0:12])
        yellow = np.sum(hist[12:31])
        green = np.sum(hist[31:70])
        blue = np.sum(hist[70:120])
        purple = np.sum(hist[120:162])
        red = np.sum(hist[162:179])

        colors = [orange, yellow, green, blue, purple, red]
        color_names = ['orange', 'yellow', 'green', 'blue', 'purple', 'red']
        color_hues = [6, 22, 50, 95, 140, 170]
        color_rgb = [(255, 255/2, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (255, 0, 0)]
        color_bgr = [(0, 255/2, 255), (0, 255, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255), (0, 0, 255)]

        color = np.argmax(colors)

        probability = float(colors[color]) / total

        #print('Color: ' + str(color) + '(' + str(probability * 100) + ')')

        return (color_names[color], probability)

    def color_callback(self, data):
        
        # Convert from ROS image to OpenCV image
        self.image = self.bridge.imgmsg_to_cv2(data, 'bgr8')

    def color_threshold(self, image):

        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        hue_min = cv2.getTrackbarPos('hue_min', 'thresh')
        hue_max = cv2.getTrackbarPos('hue_max', 'thresh')
        sat_min = cv2.getTrackbarPos('sat_min', 'thresh')
        sat_max = cv2.getTrackbarPos('sat_max', 'thresh')
        val_min = cv2.getTrackbarPos('val_min', 'thresh')
        val_max = cv2.getTrackbarPos('val_max', 'thresh')


        lower = np.array([hue_min, sat_min, val_min])
        upper = np.array([hue_max, sat_max, val_max])

        mask = cv2.inRange(hsv_image, lower, upper)

        thresh = cv2.bitwise_and(image, image, mask=mask)

        return (thresh, mask)

def main():
    print('Running... Press CTRL-C to quit.')
    ColorRecognizer()
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print('Quitting')
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
