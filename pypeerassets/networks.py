from collections import namedtuple

Network = namedtuple('Network', [
    'network_name',
    'network_shortname',
    'pubkeyhash',
    'wif_prefix',
    'scripthash',
    'magicbytes',
    'tx_timestamp',
    'denomination',
])


'''
Network name should be capitalized, for testnet append "-testnet".
For abbreviation prefix testnet of the network with "t".
'''

networks = (
    # Peercoin mainnet
    Network("Peercoin", "ppc", b'37', b'b7', b'75', b'e6e8e9e5', True, 1000000),
    # Peercoin testnet
    Network("Peercoin-testnet", "tppc", b'6f', b'ef', b'c4', b'cbf2c0ef', True, 1000000),
    # Bitcoin mainnet
    Network("Bitcoin", "btc", b'00', b'80', b'05', b'd9b4bef9', False, 100000000),
    # Bitcoin testnet
    Network("Bitcoin-testnet", "tbtc", b'6f', b'ef', b'c4', b'dab5bffa', False, 100000000)
)

def query(query):
    '''find matching parameter among the networks'''

    for network in networks:
        for field in network:
            if field == query:
                return network
