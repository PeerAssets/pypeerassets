from setuptools import setup

setup(name='pypeerassets',
      version='0.4.8',
      description='Python implementation of the PeerAssets protocol.',
      keywords=["blockchain", "digital assets", "protocol"],
      url='https://github.com/peerassets/pypeerassets',
      author='PeerAssets',
      author_email='peerchemist@protonmail.ch',
      license='BSD',
      packages=['pypeerassets', 'pypeerassets.provider'],
      install_requires=['protobuf', 'peerassets-btcpy', 'peercoin_rpc']
      )
