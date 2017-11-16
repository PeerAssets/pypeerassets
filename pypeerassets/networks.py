from collections import namedtuple
from decimal import Decimal, getcontext
getcontext().prec = 6


Network = namedtuple('Network', [
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
    Network("peercoin", "ppc", b'37', b'b7', b'75', b'e6e8e9e5',
            b'\x17PPCoin Signed Message:\n', Decimal(0.01), Decimal(0.01), True, 1000000),
    # Peercoin testnet
    Network("peercoin-testnet", "tppc", b'6f', b'ef', b'c4', b'cbf2c0ef',
            b'\x17PPCoin Signed Message:\n', Decimal(0.01), Decimal(0.01), True, 1000000),
    # Bitcoin mainnet
    Network("bitcoin", "btc", b'00', b'80', b'05', b'd9b4bef9',
            b'\x18Bitcoin Signed Message:\n', 0, 0, False, 100000000),
    # Bitcoin testnet
    Network("bitcoin-testnet", "tbtc", b'6f', b'ef', b'c4', b'dab5bffa',
            b'\x18Bitcoin Signed Message:\n', 0, 0, False, 100000000)
)


def query(query):
    '''find matching parameter among the networks'''

    for network in networks:
        for field in network:
            if field == query:
                return network
