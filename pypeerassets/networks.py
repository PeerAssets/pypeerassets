from collections import namedtuple
from decimal import Decimal

from pypeerassets.exceptions import UnsupportedNetwork


NetworkParams = namedtuple('NetworkParams', [
    'network_name',
    'network_shortname',
    'pubkeyhash',
    'wif_prefix',
    'scripthash',
    'magicbytes',
    'msgPrefix',
    'min_tx_fee',
    'min_vout_value',
    'tx_timestamp',
    'denomination',
])


'''
Network name should be lowercase, for testnet append "-testnet".
For abbreviation prefix testnet of the network with "t".
'''

networks = (
    # Peercoin mainnet
    NetworkParams("peercoin", "ppc", b'37', b'b7', b'75', b'e6e8e9e5',
                  b'\x17PPCoin Signed Message:\n', Decimal(0.01),
                  0, True, Decimal('1e6')),
    # Peercoin testnet
    NetworkParams("peercoin-testnet", "tppc", b'6f', b'ef', b'c4', b'cbf2c0ef',
                  b'\x17PPCoin Signed Message:\n', Decimal(0.01),
                  0, True, Decimal('1e6')),
    # Bitcoin mainnet
    NetworkParams("bitcoin", "btc", b'00', b'80', b'05', b'd9b4bef9',
                  b'\x18Bitcoin Signed Message:\n', 0, 0, False, Decimal('1e8')),
    # Bitcoin testnet
    NetworkParams("bitcoin-testnet", "tbtc", b'6f', b'ef', b'c4', b'dab5bffa',
                  b'\x18Bitcoin Signed Message:\n', 0, 0, False, Decimal('1e8'))
)


def net_query(name: str) -> NetworkParams:
    '''Find the NetworkParams for a network by its long or short name. Raises
    UnsupportedNetwork if no NetworkParams is found.
    '''

    for net_params in networks:
        if name in (net_params.network_name, net_params.network_shortname,):
            return net_params

    raise UnsupportedNetwork
