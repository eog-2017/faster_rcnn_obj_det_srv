#!/usr/bin/env python

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""
Demo script showing detections in sample images.

See README.md for installation instructions before running.
"""

import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String,Int32,Int32MultiArray,MultiArrayLayout,MultiArrayDimension,Float64,Float64MultiArray

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

NETS = {'vgg16': ('VGG16',
                  'VGG16_faster_rcnn_final.caffemodel'),
        'zf': ('ZF',
                  'ZF_faster_rcnn_final.caffemodel'),
	'apc' : ('apc',
		  'vgg16_faster_rcnn_iter_full_data.caffemodel')}

def image_service_callback(req):
    
    caffe.set_mode_gpu()
    caffe.set_device(args.gpu_id)

    # Instantiate CvBridge
    bridge = CvBridge()
    try:
        # Convert your ROS Image message to OpenCV2
        cv2_img = bridge.imgmsg_to_cv2(req.input_rgb_img, "bgr8")
    except CvBridgeError, e:
        print(e)
    else:
        # Save your OpenCV2 image as a jpeg
 	print "Converted ROS Image to OpenCV Image"

    bbox_classid_array = Int32MultiArray(data=[])
    score_array = Float64MultiArray(data=[])

    #cv2.imshow("window", cv2_img)
    #cv2.waitKey(0)

    
    bbox_classid, score = demo(net, cv2_img)

    index = 0

    while index < len(score):
	bbox_classid_array.data.extend(bbox_classid[index].tolist())
	index = index + 1
    score_array.data.extend(score)
    #print bbox_classid_array
    #print score_array
    return bbox_scoresResponse(bbox_classid_array, score_array)


def demo(net, im):
    """Detect object classes in an image using pre-computed object proposals."""

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    
    bbox_classid = []
    score = []

    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes, cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
	inds = np.where(dets[:, -1] >= CONF_THRESH)[0]
	maxBox = []
	maxScore = 0.000
	for i in inds:
	    if dets[i, -1] > maxScore:
	    	maxScore = dets[i, -1]
		maxBox = np.append(np.round(dets[i, :4]).astype(np.int), cls_ind)

	if len(maxBox) is not 0:
	    bbox_classid.append(maxBox)
	if maxScore > 0:
	    score.append(maxScore)
	
    return bbox_classid, score

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        choices=NETS.keys(), default='apc')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()

    prototxt = os.path.join(cfg.MODELS_DIR, '..', NETS[args.demo_net][0], 'VGG16', 'faster_rcnn_end2end', 'test_apc_30.prototxt')
    
    caffemodel = os.path.join(cfg.DATA_DIR, '..', 'output', 'faster_rcnn_end2end', 'apc_2017_train', NETS[args.demo_net][1])

    if not os.path.isfile(prototxt):
	raise IOError(('{:s} not found...').format(prototxt))
    
    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print '\n\nLoaded network {:s}'.format(caffemodel)

    # Warmup on a dummy image
    im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im)

    #im = cv2.imread('2297.jpg')
    #print demo(net, im)

    rospy.init_node('rcnn_object_detection')

    # Service for finding object boxes in the image
    object_detect_service = rospy.Service("/faster_rcnn_obj_det_service", bbox_scores, image_service_callback)
	
    # Spin until ctrl + c
    rospy.spin()
