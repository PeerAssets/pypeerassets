from pypeerassets import networks
try:
    from coincurve import PrivateKey
    is_ecdsa = False
except ImportError:
    is_ecdsa = True
    from crypto.ecdsa import PrivateKey
from pypeerassets.base58 import b58encode, b58decode
from random import SystemRandom
from hashlib import sha256, new
from binascii import hexlify, unhexlify


class Kutil:

    def __init__(self, privkey=None, seed=None, wif=None, network=None):
        '''wif=<WIF> import private key from your wallet in WIF format
           privkey=<privkey> import private key in binary format
           network=<network> specify network [ppc, tppc, btc]
           seed=<seed> specify seed (string) to make the privkey from'''

        if privkey is not None:
            self.keypair = PrivateKey(unhexlify(privkey))

        if seed is not None:
            self.keypair = PrivateKey(sha256(seed.encode()).hexdigest())

        if wif is not None:
            key = self.wif_to_privkey(wif)
            self.keypair = PrivateKey(key["privkey"])
            network = key['net_prefix']

        if privkey == seed == wif == None:
            self.keypair = PrivateKey()
        
        if not is_ecdsa:
            self._privkey = self.keypair.to_hex().encode()
            self.pubkey = hexlify(self.keypair.public_key.format())
        else:
            self._privkey = self.keypair.private_key
            self.pubkey = self.keypair.public_key
        
        self.load_network_parameters(network)

    def load_network_parameters(self, query: str):
        import networks
        '''loads network parameters and sets class variables'''

        for field, var in zip(networks.query(query)._fields, networks.query(query)):
            setattr(self, field, var)

    def wif_to_privkey(self, wif: str):
        '''import WIF'''
        if not 51 <= len(wif) <= 52:
            return 'Invalid WIF length'

        b58_wif = b58decode(wif)
        return {'privkey': b58_wif[1:33], 'net_prefix': hexlify(b58_wif[0:1])}

    @property
    def address(self) -> str:
        '''generate an address from pubkey'''

        key = unhexlify(self.pubkey)  # compressed pubkey as default

        keyhash = unhexlify(self.pubkeyhash + hexlify(new('ripemd160',
                                                      sha256(key).digest()).digest()))

        checksum = sha256(sha256(keyhash).digest()).digest()[0:4]
        address = keyhash + checksum
        return b58encode(address)

    @property
    def wif(self) -> str:
        '''convert raw private key to WIF'''

        extkey = unhexlify(self.wif_prefix + self._privkey + b'01')  # compressed by default
        extcheck = extkey + sha256(sha256(extkey).digest()).digest()[0:4]
        wif = b58encode(extcheck)

        return wif
