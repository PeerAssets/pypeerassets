from hashlib import sha256, new
from binascii import hexlify, unhexlify
from base58 import b58encode, b58decode
from secp256k1 import PrivateKey
from . import networks

class Kutil:
    '''pubkey/privkey operations'''

    def __init__(self, wif=None, privkey=None, network=None, seed=None):
        '''wif=<WIF> import private key from your wallet in WIF format
           privkey=<privkey> import private key in binary format
           network=<network> specify network [ppc, tppc, btc]
           seed=<seed> specify seed (string) to make the privkey from'''

        if wif is not None:
            key = self.wif_to_privkey(wif)
            self.keypair = PrivateKey(key['privkey'])
            network = key['net_prefix']

        if seed is not None:
            self.keypair = PrivateKey(raw=bytes([seed]))

        if privkey is not None:
            self.keypair = PrivateKey(unhexlify(privkey))

        if privkey == wif == seed == None:
            self.keypair = PrivateKey() # new keypair

        if network is None:
            self.load_network_parameters('ppc')
        else:
            self.load_network_parameters(network)

        self._privkey = self.keypair.private_key
        self._pubkey = self.keypair.pubkey.serialize(compressed=False)
        self._pubkey_compressed = self.keypair.pubkey.serialize(compressed=True)

    def load_network_parameters(self, query):
        '''loads network parameters and sets class variables'''

        for field, var in zip(networks.query(query)._fields, networks.query(query)):
            setattr(self, field, var)

    @property
    def privkey(self):
        '''retrun privkey in hex format'''

        return hexlify(self._privkey).decode("utf-8")

    @property
    def pubkey(self):
        '''return compressed pubkey in hex format'''

        return hexlify(self._pubkey_compressed).decode("utf-8")

    @property
    def address(self):
        '''generate an address from pubkey'''

        key = self._pubkey_compressed # compressed pubkey as default

        keyhash = unhexlify(self.pubkeyhash + hexlify(
            new('ripemd160', sha256(key).digest()).
            digest())
                           )

        checksum = sha256(
            sha256(keyhash).digest()
            ).hexdigest()[0:8]

        return b58encode(keyhash + unhexlify(checksum))

    @staticmethod
    def check_wif(wif):
        '''check if WIF is properly formated.'''

        b58_wif = b58decode(wif)
        check = b58_wif[-4:]
        checksum = sha256(sha256(b58_wif[:-4]).digest()).digest()[0:4]
        return checksum == check

    @property
    def wif(self):
        '''convert raw private key to WIF'''

        extkey = self.wif_prefix + hexlify(self._privkey) + b'01' # compressed by default
        extcheck = unhexlify(extkey) + sha256(sha256(unhexlify(extkey
                                                              )).digest()).digest()[0:4]
        wif = b58encode(extcheck)

        assert self.check_wif(wif)
        return wif

    def wif_to_privkey(self, wif):
        '''import WIF'''

        assert self.check_wif(wif)
        b58_wif = b58decode(wif)

        if len(wif) == 51:
            return {'privkey': b58_wif[1:-4], 'net_prefix': hexlify(b58_wif[0:1])}
        if len(wif) == 52:
            return {'privkey': b58_wif[1:-5], 'net_prefix': hexlify(b58_wif[0:1])}
        else:
            return 'Invalid WIF length'

    def sign(self, message):
        '''sing >message< with the privkey'''

        return self.keypair.ecdsa_sign(message.encode('utf-8'))

    def verify(self, message, signature):
        '''verify >message< against >signature<'''

        return self.keypair.pubkey.ecdsa_verify(message.encode('utf-8'), signature)
