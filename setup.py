from setuptools import setup
from jhsiao.namespace import make_ns, fdir
make_ns('jhsiao', 'jhsiao/labeleritems', dir=fdir(__file__))
setup(
    name='jhsiao.labeler',
    version='0.0.1',
    author='Jason Hsiao',
    author_email='oaishnosaj@gmail.com',
    description='Label sets of images.',
    packages=['jhsiao.labeler', 'jhsiao.labeleritems'],
    install_requires=['jhsiao.tkutil @ git+https://github.com/j-hsiao/py-tkutil.git']
)
