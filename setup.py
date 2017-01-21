from setuptools import setup

setup(name='pypeerassets',
      version='0.0.1',
      description='Python implementation of the PeerAssets protocol.',
      url='https://github.com/peerassets/pypeerassets',
      author='PeerAssets',
      author_email='peerchemist@protonmail.ch',
      license='GPL',
      packages=['pypeerassets'],
      install_requires=['requests', 'secp256k1', 'base58', 'protobuf'],
      zip_safe=True)
