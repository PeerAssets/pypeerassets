import random
from . import networks
from .ecdsa import ECDSA
from .base58 import b58encode
from hashlib import sha256, new
from binascii import hexlify, unhexlify


class Kutil:
    def __init__(self, privkey=None,seed=None, network=None):

        if privkey is not None:
            self.privkey = privkey
    
        if seed is not None:
            self.privkey = sha256(seed.encode()).hexdigest()
        
        if privkey == seed == None:
            self.privkey = '{:0>64x}'.format(random.getrandbits(256))

        self._privkey = int(self.privkey,16)
        self.privkey = self.privkey.encode()
        self.pubkey = ECDSA(self._privkey).pubkey()

        if network is None:
            self.load_network_parameters('ppc')
        else:
            self.load_network_parameters(network)
        
    def load_network_parameters(self, query):
        '''loads network parameters and sets class variables'''

        for field, var in zip(networks.query(query)._fields, networks.query(query)):
            setattr(self, field, var)
    
    @property
    def address(self):
        '''generate an address from pubkey'''

        key = unhexlify(self.pubkey) # compressed pubkey as default

        keyhash = unhexlify(self.pubkeyhash + hexlify(new('ripemd160', sha256(key).digest()).digest()))

        checksum = sha256(sha256(keyhash).digest()).digest()[0:4]
        address = keyhash + checksum
        return b58encode(address).encode()
    
    @property
    def wif(self):
        '''convert raw private key to WIF'''

        extkey = unhexlify(self.wif_prefix + self.privkey + b'01') # compressed by default
        extcheck = extkey + sha256(sha256(extkey).digest()).digest()[0:4]
        wif = b58encode(extcheck)
        
        return wif.encode()
