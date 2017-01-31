#!/usr/bin/env python

import os
import sys
import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from faster_rcnn_obj_det_srv.srv import *

CLASSES =('__background__', # always index 0
          'barkely_bones', 'bunny_book', 'cherokee_tshirt',
          'clorox_brush', 'cloud_bear', 'command_hooks',
          'crayola_24_ct', 'creativity_stems', 'dasani_bottle',
          'easter_sippy_cup', 'elmers_school_glue', 'expo_eraser',
          'fitness_dumbell', 'folgers_coffee', 'glucose_up_bottle',
          'jane_dvd', 'jumbo_pencil_cup', 'kleenex_towels',
          'kygen_puppies', 'laugh_joke_book', 'pencils',
          'platinum_bowl', 'rawlings_baseball', 'safety_plugs',
          'scotch_tape', 'staples_cards', 'viva',
          'white_lightbulb', 'woods_cord')

if __name__ == "__main__":
    rospy.wait_for_service('/faster_rcnn_obj_det_service')

    imgs = os.listdir('.')
    print imgs

    for img1 in imgs:
	if 'jpg' not in img1:
	    continue

    	img = cv2.imread(img1)
    
    	bridge = CvBridge()
    	try:
            # Convert your ROS Image message to OpenCV2
            imgmsg = bridge.cv2_to_imgmsg(img, "bgr8")
        except CvBridgeError, e:
            print(e)
    
        try:
	    call = rospy.ServiceProxy('/faster_rcnn_obj_det_service', bbox_scores)
	    resp1 = call(imgmsg)
	    print resp1
	except rospy.ServiceException, e:
	    print e

        bbox = resp1.obj_box_rect.data

    	i = 0

    	while i < len(bbox)/5:
	    j = i * 5	
	    cv2.rectangle(img, (bbox[j], bbox[j+1]), (bbox[j+2] , bbox[j+3]), (0,255,0), 3)
	    cv2.putText(img, CLASSES[bbox[j+4]], (bbox[j], bbox[j+1]), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 0, 0), 2)
	    i = i + 1

	cv2.imshow("win", img)
	cv2.waitKey(0)
