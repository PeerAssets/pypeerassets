import pytest
from pypeerassets.kutil import Kutil


def test_network_parameter_load():
    '''tests if loading of network parameteres is accurate.'''

    mykey = Kutil(network="ppc")

    assert mykey.denomination == 1000000
    assert mykey.wif_prefix == b'b7'
    assert mykey.pubkeyhash == b'37'


def test_key_generation():
    '''test privkey/pubkey generation.'''

    mykey = Kutil(network="ppc")

    assert isinstance(mykey.privkey, bytes)
    assert isinstance(mykey.pubkey, bytes)

@pytest.mark.xfail
def test_key_generation_from_seed():
    '''check if key generation is what is expected from seed.'''

    seed = "Hello PeerAssets."
    mykey = Kutil(seed=seed, network="ppc")

    assert mykey.privkey == b'680510f7f5e622347bc8d9e54e109a9192353693ef61d82d2d5bdf4bc9fd638b'
    assert mykey.pubkey == b'037cf9e7664b5d10ce209cf9e2c7f68baa06f1950114f25677531b959edd7e670c'


def test_address_generation():
    '''test if addresses are properly made'''

    mykey = Kutil(network="ppc")

    assert mykey.address.startswith("P")
    assert isinstance(mykey.address, str)
    assert len(mykey.address) == 34


def test_wif_import():
    '''test improting WIF privkey'''

    mykey = Kutil(network="ppc", wif="7A6cFXZSZnNUzutCMcuE1hyqDPtysH2LrSA9i5sqP2BPCLrAvZM")

    assert mykey.address == 'PJxwxuBqjpHhhdpV6KY1pXxUSUNb6omyNW'
    assert mykey.pubkey == b'02a119079ef5be1032bed61cc295cdccde58bf70e0dd982399c024d1263740f398'
    assert mykey.privkey == b'b43d38cdfa04ecea88f7d9d7e95b15b476e4a6c3f551ae7b45344831c3098da2'
