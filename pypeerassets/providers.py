
'''Service providers used for block fetching, transaction submitting and acquiring UTXO's.'''

class Mock:
    '''Mock provider, with usable but fake data, used for testing'''
    pass

class Peercoin_rpc:
    '''Communicate with local or remote peercoin-daemon via JSON-RPC'''
    pass

class Mercator:
    '''Use PeerAssets/mercator as remote backend.'''
    pass

