from btcpy.structs.address import (
    Address,
    InvalidAddress,
    P2pkhAddress,
    P2shAddress,
)
import pytest

from pypeerassets.btcpy_peercoin import PeercoinTx
from pypeerassets.networks import PeercoinMainnet, PeercoinTestnet


def test_peercoin_address_success():
    good_addresses = {
        ('PeercoinMainnet', P2pkhAddress, 'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw',),
        ('PeercoinTestnet', P2pkhAddress, 'mj46gUeZgeD9ufU7Fvz2dWqaX6Nswtbpba',),
        ('PeercoinTestnet', P2pkhAddress, 'n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj',),
        ('PeercoinMainnet', P2shAddress, 'p92W3t7YkKfQEPDb7cG9jQ6iMh7cpKLvwK',),
    }
    for net, addr_type, address in good_addresses:
        net = PeercoinMainnet if net == 'PeercoinMainnet' else PeercoinTestnet
        from_string = Address.from_string(address, network=net)
        assert address == str(from_string)
        assert from_string.__class__ == addr_type
        assert from_string.network == net


def test_peercoin_address_failure():
    bad_addresses = {
        'vioqwV3F4YzpgnfyUukGVMB3Hv83ujehKCiGWyrYyx2Z7hiKQy7SWUV9KgfMdV9J',
        'bc1a',
        '3rE3tz',
        '1KKKK6N21XKo48zWKuQKXdvSsCf95ibHFa',
    }
    for address in bad_addresses:
        with pytest.raises(InvalidAddress):
            Address.from_string(address, network=PeercoinMainnet)


def test_peercoin_tx_unhexilify():
    """Check that we can parse a PeercoinTx from hex encoded bytes. Data from:

    In [1]: import pypeerassets as pa

    In [2]: provider = pa.Explorer(network='tppc')

    In [3]: raw = provider.getrawtransaction('c418f3bded92ebc035cfefc93f54dc8a501702e6ad4e6a26a07aab87f4cfb653')
    """
    raw = '01000000f7ae3b5b01b3a00d828f5a9a8e908fb59353b4a87132a75a6d939c6e9338e3727631a65028010000006c493046022100e3a72a3a9f53eab66186da5354a58a6fb4b4fc96c5836445bce0b3755840653f022100f7013eb0c3bbd901a8e9c4935edefa9765fa5dd2f1f3a276634d248a4e17c59801210207c75090d56b94a9f638b8b9abaa346c053db265f4aa752170b86c32cdec7efbffffffff0260d3e815000000001976a914c8ec65800888c2c4f831826ba7e10603b3692db188ac00e1f505000000001976a914ba96e0c304ad07afb115d7019b9e54db96668f9988ac00000000'
    PeercoinTx.unhexlify(raw, network=PeercoinTestnet)
