try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='OCRadio',
      version='0.9.1',
      description='OCRadio streaming MP3 Server',
      author='David Massey <davidm@msynet.com>',
      author_email='davidm@msynet.com',
      url='http://www.msynet.com/ocxradio/',
      license='GPL',
      install_requires=['mutagen', 'python-daemon'],
      scripts=['bin/ocradio'],
      packages=['ocradio']
      )
