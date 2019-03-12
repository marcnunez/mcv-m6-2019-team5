from typing import List

import cv2

from model import Video, Rectangle, Frame
from operations.find_boxes import find_boxes
from operations.gaussian_model import get_background_model, gaussian_model
from operations.morphological_operations import closing, opening
from utils import read_detections


def week2_nonadaptive(video: Video) -> List[List[Rectangle]]:
    model_mean, model_std = get_background_model(video, int(2141 * 0.25), total_frames=int(2141 * 0.25))

    ground_truth = read_detections('../datasets/AICity_data/train/S03/c010/gt/gt.txt')
    frames = []

    frame_id = int(2141 * 0.25)
    roi = cv2.cvtColor(cv2.imread('../datasets/AICity_data/train/S03/c010/roi.jpg'), cv2.COLOR_BGR2GRAY)
    for mask in gaussian_model(video, int(2141 * 0.25), model_mean, model_std, total_frames=int(2141 * 0.10)):
        mask = mask & roi
        cv2.imshow('f', mask)
        cv2.waitKey()
        mask = closing(mask, 30)
        cv2.imshow('f', mask)
        cv2.waitKey()


        mask = opening(mask, 5)
        cv2.imshow('f', mask)
        cv2.waitKey()
        bbs = find_boxes(mask)

        frame = Frame(frame_id)
        frame.detections = bbs
        frame.ground_truth = ground_truth[frame_id]

        frames.append(frame)

        frame_id += 1

        result = frame.to_result(ignore_classes=True)
        iou = frame.get_detection_iou(ignore_classes=True)
        print(iou)
