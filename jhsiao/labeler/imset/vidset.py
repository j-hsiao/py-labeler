import cv2

from . import ImageSet

class VidSet(ImageSet):
    def __init__(self, vidname):
        self.vidname = vidname
        self.cap = cv2.VideoCapture()
        if not self.cap.open(vidname):
            raise ValueError('Bad video: {}'.format(vidname))

    def get(self, name, callback):
        target = int(name)
        cur = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        if target != cur:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        s, f = self.cap.read()
        callback(name, f)

    def __iter__(self):
        nframes = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fmt = '{{:0{}d}}'.format(len(str(nframes))).format
        for i in range(nframes):
            yield fmt(i)
