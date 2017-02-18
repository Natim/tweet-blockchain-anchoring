import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    """Open a related file and return its content."""
    with codecs.open(os.path.join(here, filename), encoding='utf-8') as f:
        content = f.read()
    return content


README = read_file('README.rst')
CHANGELOG = CONTRIBUTORS = ''

REQUIREMENTS = [
    'aiohttp',
    'cchardet',
    'aiodns',
]

setup(name='tweet-blockchain-anchoring',
      version='0.1.0.dev0',
      description='Backup and Anchor people tweets in the blockchain.',
      long_description=README + "\n\n" + CHANGELOG + "\n\n" + CONTRIBUTORS,
      license='Apache License (2.0)',
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "License :: OSI Approved :: Apache Software License"
      ],
      keywords="web twitter blockchain anchoring",
      author='Rémy Hubscher',
      author_email='hubscher.remy@gmail.com',
      url='https://github.com/Natim/tweet-blockchain-anchoring',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIREMENTS)