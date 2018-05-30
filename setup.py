from setuptools import setup

setup(name='pypeerassets',
      version='0.4.0',
      description='Python implementation of the PeerAssets protocol.',
      keywords=["blockchain", "digital assets", "protocol"],
      url='https://github.com/peerassets/pypeerassets',
      author='PeerAssets',
      author_email='peerchemist@protonmail.ch',
      license='BSD',
      packages=['pypeerassets', 'pypeerassets.provider'],
      install_requires=['protobuf', 'peerassets-btcpy'],
      extras_require={
        'rcp_provider': ['peercoin_rpc>=0.56']
                        },
      zip_safe=True)
