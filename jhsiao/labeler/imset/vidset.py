import cv2

from . import ImageSet

class VidSet(ImageSet):
    def __init__(self, vidname):
        super(VidSet, self).__init__(vidname)
        self.cap = cv2.VideoCapture()
        if not self.cap.open(vidname):
            raise ValueError('Bad video: {}'.format(vidname))
        self._get_thread()

    def __len__(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    @staticmethod
    def _load(idx, cap):
        """Load a frame from video."""
        nextidx = cap.get(cv2.CAP_PROP_POS_FRAMES)
        if nextidx != idx:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        s, f = cap.read()
        return str(idx), f

    @ImageSet.lencheck
    def __getitem__(self, idx):
        if idx < 0 or len(self) <= idx:
            raise IndexError(str(idx))
        self.pos = idx
        return self._load(idx, self.cap)

    @ImageSet.lencheck
    def __call__(self, idx, callback):
        self.pos = idx
        with self.cond:
            self.q.append(
                (callback, self._load, (idx, self.cap), {}))
            self.cond.notify()
        return str(idx)
