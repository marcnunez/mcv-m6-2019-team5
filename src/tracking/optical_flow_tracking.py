from typing import List

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches, colors

from model import Frame, Detection, SiameseDB
from utils import IDGenerator, show_optical_flow_arrows

INTERSECTION_THRESHOLD = 0.5


class OpticalFlowTracking:
    """
    look_back: int. How many frames back to search for an intersection
    """

    def __init__(self, win_size=15, max_level=3, look_back=3):
        self.look_back = look_back
        self.prev_img = None
        self.prev_det = None
        # params for ShiTomasi corner detection
        self.feature_params = dict(maxCorners=500, qualityLevel=0.3, minDistance=7, blockSize=7)
        # Parameters for lucas kanade optical flow
        self.lk_params = dict(winSize=(win_size, win_size), maxLevel=max_level,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        viridis = colors.ListedColormap(np.random.rand(256, 3))
        self.new_color = viridis(np.linspace(0, 1, 256))

    def __call__(self, frame: Frame, siamese: SiameseDB, debug=False, plot_number=False) -> None:
        self.debug = debug
        det1_flow = []
        if self.prev_img is not None:
            flow = self._optical_flow(frame.image)
            if debug:
                show_optical_flow_arrows(frame.image, flow)
            for det in self.prev_det:
                det_flow = flow[det.top_left[1]:det.top_left[1] + det.height,
                           det.top_left[0]:det.top_left[0] + det.width, :]
                accum_flow = (0, 0)
                non_zero_values = det_flow[np.logical_or(det_flow[:, :, 0] != 0, det_flow[:, :, 1] != 0), :]
                if non_zero_values.size > 0:
                    accum_flow = np.mean(non_zero_values, axis=0)
                det1_flow.append(
                    Detection(det.id, det.label,
                              (int(det.top_left[0] + accum_flow[1]), int(det.top_left[1] + accum_flow[0])),
                              det.width, det.height))

        for detection in frame.detections:
            self._find_id(detection, det1_flow)
            if detection.id == -1:
                if siamese is not None:
                    new_id = siamese.query(frame.image, detection)
                    if new_id != -1:
                        detection.id = new_id
                    else:
                        detection.id = IDGenerator.next()
                else:
                    detection.id = IDGenerator.next()
        self.prev_det = frame.detections
        self.prev_img = frame.image

        if debug:
            self.plot_tracking_color(frame, plot_number)

    @staticmethod
    def plot_tracking(frame: Frame):
        plt.imshow(cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB))
        plt.axis('off')
        for det in frame.detections:
            rect = patches.Rectangle((det.top_left[0], det.top_left[1]), det.width, det.height,
                                     linewidth=1, edgecolor='blue', facecolor='none')
            plt.gca().add_patch(rect)

            plt.text(det.top_left[0] - 0, det.top_left[1] - 50, s='{}'.format(det.id),
                     color='white', verticalalignment='top',
                     bbox={'color': 'blue', 'pad': 0})
            plt.gca().add_patch(rect)
        plt.imshow(cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB))
        plt.axis('off')
        plt.show()
        plt.close()

    def plot_tracking_color(self, frame: Frame, plot_number):
        plt.imshow(cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB))
        plt.axis('off')

        for det in frame.detections:
            if det.id != -1:
                rect = patches.Rectangle((det.top_left[0], det.top_left[1]), det.width, det.height,
                                         linewidth=2, edgecolor=self.new_color[det.id, :], facecolor='none')
                plt.gca().add_patch(rect)
                if plot_number:
                    plt.text(det.top_left[0] - 0, det.top_left[1] - 50, s='{}'.format(det.id),
                             color='white', verticalalignment='top',
                             bbox={'color': 'blue', 'pad': 0})

                plt.gca().add_patch(rect)
        plt.imshow(cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB))
        plt.axis('off')
        plt.show()
        plt.close()

    def _find_id(self, detection: Detection, dets_old: List[Detection]) -> None:
        if self.prev_det is None:
            return
        for detection2 in dets_old:
            if detection.iou(detection2) > INTERSECTION_THRESHOLD:
                detection.id = detection2.id
                break

    def _optical_flow(self, image) -> np.ndarray:
        of = np.zeros((image.shape[0], image.shape[1], 2))
        p0 = self._get_features()
        if p0 is None or p0.size == 0:
            return of
        p1, st, err = cv2.calcOpticalFlowPyrLK(cv2.cvtColor(self.prev_img, cv2.COLOR_BGR2GRAY),
                                               cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), p0, None, **self.lk_params)
        # Select good points
        good_new = p1[st == 1]
        good_old = p0[st == 1]
        for i, (new, old) in enumerate(zip(good_new, good_old)):
            b, a = new.ravel()
            d, c = old.ravel()
            of[int(c), int(d), :] = (b - d, a - c)
        return of

    def _get_features(self):
        mask = np.zeros((self.prev_img.shape[0], self.prev_img.shape[1]), dtype=np.uint8)
        for det in self.prev_det:
            mask[det.top_left[1]:det.top_left[1] + det.height, det.top_left[0]:det.top_left[0] + det.width] = 255
        if self.debug:
            plt.imshow(mask)
            plt.show()
            plt.close()
        p0 = cv2.goodFeaturesToTrack(cv2.cvtColor(self.prev_img, cv2.COLOR_BGR2GRAY), mask=mask, **self.feature_params)
        return p0
