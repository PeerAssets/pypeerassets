import pytest
from os import urandom
from pypeerassets.kutil import Kutil


def test_key_generation():
    '''test privkey/pubkey generation.'''

    mykey = Kutil(network="ppc")

    assert isinstance(mykey.privkey, str)
    assert isinstance(mykey.pubkey, str)


def test_key_generation_from_seed():
    '''check if key generation is what is expected from seed.'''

    seed = "Hello PeerAssets."
    mykey = Kutil(from_string=seed, network="tppc")

    assert mykey.privkey == '680510f7f5e622347bc8d9e54e109a9192353693ef61d82d2d5bdf4bc9fd638b'
    assert mykey.pubkey == '037cf9e7664b5d10ce209cf9e2c7f68baa06f1950114f25677531b959edd7e670c'


def test_address_generation():
    '''test if addresses are properly made'''

    privkey = bytearray(urandom(32))

    assert Kutil(network="ppc", privkey=privkey).address.startswith("P")

    assert isinstance(Kutil(network='ppc').address, str)
    assert len(Kutil(network='ppc').address) == 34


def test_mainnet_wif_import():
    '''test importing WIF privkey'''

    mykey = Kutil(network='ppc', from_wif="U624wXL6iT7XZ9qeHsrtPGEiU78V1YxDfwq75Mymd61Ch56w47KE")

    assert mykey.address == 'PAprodbYvZqf4vjhef49aThB9rSZRxXsM6'
    assert mykey.pubkey == '023aaca6c4f022543f4a2920f66544a6ce89746f7fce4da35d63b5886fdac06634'
    assert mykey.privkey == '1b19749afd007bf6db0029e0273a46409bc160b9349031752bbc3cd913bbbdd3'
