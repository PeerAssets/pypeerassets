from . import networks
from .ecdsa import ECDSA
from .base58 import b58encode, b58decode
from random import SystemRandom
from hashlib import sha256, new
from binascii import hexlify, unhexlify


class Kutil:

    def __init__(self, privkey=None, seed=None, wif=None, network=None):

        if privkey is not None:
            self.privkey = privkey

        if seed is not None:
            self.privkey = sha256(seed.encode()).hexdigest()

        if wif is not None:
            key = self.wif_to_privkey(wif)
            self.privkey = key["privkey"]
            network = key['net_prefix']

        if privkey == seed == wif == None:
            self.privkey = '{:0>64x}'.format(SystemRandom().getrandbits(256))

        assert network is not None, "network parameter required"

        self._privkey = int(self.privkey, 16)
        self.privkey = self.privkey.encode()
        self.pubkey = ECDSA(self._privkey).pubkey()
        self.load_network_parameters(network)

    def load_network_parameters(self, query: str):
        '''loads network parameters and sets class variables'''

        for field, var in zip(networks.query(query)._fields, networks.query(query)):
            setattr(self, field, var)

    def wif_to_privkey(self, wif: str) -> bytes:
        '''import WIF'''

        b58_wif = b58decode(wif)

        if len(wif) == 51:
            return {'privkey': hexlify(b58_wif[1:-4]).decode(), 'net_prefix': hexlify(b58_wif[0:1])}
        if len(wif) == 52:
            return {'privkey': hexlify(b58_wif[1:-5]).decode(), 'net_prefix': hexlify(b58_wif[0:1])}
        else:
            return 'Invalid WIF length'

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

        extkey = unhexlify(self.wif_prefix + self.privkey + b'01')  # compressed by default
        extcheck = extkey + sha256(sha256(extkey).digest()).digest()[0:4]
        wif = b58encode(extcheck)

        return wif
