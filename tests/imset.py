from __future__ import division
import os

import cv2

from jhsiao.labeler import imset


def test_imsets():
    ims = imset.open(os.environ.get('IM', '.'))
    def callback(name, im):
        scale = 720 / im.shape[0]
        scaled = cv2.resize(im, (0,0), fx=scale, fy=scale)
        cv2.putText(
            scaled, name, (9, 701), cv2.FONT_HERSHEY_SIMPLEX,
            1.0, (0,0,0), 3)
        cv2.putText(
            scaled, name, (10, 700), cv2.FONT_HERSHEY_SIMPLEX,
            1.0, (255,255,255), 1)
        cv2.imshow('im', scaled)
        k = cv2.waitKey(0)
        if k == ord('q'):
            raise StopIteration
        cv2.destroyWindow(name)
    if ims is not None:
        try:
            for name in ims:
                ims.get(name, callback)
        except StopIteration:
            pass
