from __future__ import division
import os
try:
    import queue
except ImportError:
    import Queue as queue

import cv2

from jhsiao.labeler.imset import ImageSet


def test_imsets():
    ims = ImageSet.open(os.environ.get('IM', '.'))
    q = queue.Queue()
    def callback(name, im):
        if im is None:
            print('Load failed!', repr(name))
            return
        print('loaded', name)
        scale = 720 / im.shape[0]
        scaled = cv2.resize(im, (0,0), fx=scale, fy=scale)
        cv2.putText(
            scaled, name, (9, 701), cv2.FONT_HERSHEY_SIMPLEX,
            1.0, (0,0,0), 3)
        cv2.putText(
            scaled, name, (10, 700), cv2.FONT_HERSHEY_SIMPLEX,
            1.0, (255,255,255), 1)
        q.put(scaled)

    cv2.namedWindow('im')
    callback(*ims[0])
    k = -1
    while k != ord('q'):
        try:
            im = q.get(False)
        except queue.Empty:
            pass
        else:
            cv2.imshow('im', im)
        k = cv2.waitKey(30) & 0xFF
        if k == ord('a'):
            try:
                print('pending', ims(ims.pos-1, callback))
            except IndexError:
                print('left border')
        elif k == ord('d'):
            try:
                print('pending', ims(ims.pos+1, callback))
            except IndexError:
                print('right border')
        print(ims.pos)
