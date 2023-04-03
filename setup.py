from setuptools import setup
from jhsiao.namespace import make_ns
make_ns('jhsiao', 'jhsiao/labeleritems')
setup(
    name='jhsiao-labeler',
    version='0.0.2',
    author='Jason Hsiao',
    author_email='oaishnosaj@gmail.com',
    description='Label sets of images.',
    packages=['jhsiao', 'jhsiao.labeler', 'jhsiao.labeleritems'],
    install_requires=[
        'jhsiao-tkutil @ git+https://github.com/j-hsiao/py-tkutil.git',
        'numpy',
        'opencv-python',
        'pillow',
    ]
)
