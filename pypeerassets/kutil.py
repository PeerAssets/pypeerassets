
'''Kutil is for all things cryptography.'''

from hashlib import sha256, new
from binascii import hexlify, unhexlify
from base64 import b64encode, b64decode
from pypeerassets.base58 import b58encode, b58decode
from secp256k1 import PrivateKey
from pypeerassets import networks
from pypeerassets.transactions import var_int

class Kutil:
    '''pubkey/privkey operations'''

    def __init__(self, network=None, wif=None, privkey=None, seed=None):
        '''wif=<WIF> import private key from your wallet in WIF format
           privkey=<privkey> import private key in binary format
           network=<network> specify network [ppc, tppc, btc]
           seed=<seed> specify seed (string) to make the privkey from'''

        if wif is not None:
            key = self.wif_to_privkey(wif)
            self.keypair = PrivateKey(key['privkey'])
            network = key['net_prefix']

        if seed is not None:
            self.keypair = PrivateKey(privkey=self.seed_to_privkey(seed))

        if privkey is not None:
            self.keypair = PrivateKey(unhexlify(privkey))

        if privkey == wif == seed == None:
            self.keypair = PrivateKey() # new keypair

        if network:
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

    @staticmethod
    def seed_to_privkey(seed):
        '''use mnemonic seed hash as privkey'''

        seed_hash = sha256(seed.encode("utf-8")).digest()
        return seed_hash

    def sign_message(self, message):
        '''sign >message< with the privkey and b64encode'''

        message = message.encode()
        prefix2 = var_int(len(message))
        buffer = b''.join([self.msgPrefix, prefix2, message])
        msg_hash = sha256(sha256(buffer).digest()).digest()
        sig = self.keypair.ecdsa_sign(msg_hash, raw=True)
        ## calculate the size of the key ?
        signature = self.keypair.ecdsa_serialize_compact(sig)

        return b64encode(var_int(len(signature)) + signature).decode()

    def ecdsa_sign(self, message):
        '''sign >message< with the privkey'''

        message = message.encode()
        msg_hash = sha256(sha256(message).digest()).digest()
        sig = self.keypair.ecdsa_sign(msg_hash, raw=True)

        return self.keypair.ecdsa_serialize_compact(sig)
    
    def verify_message(self, message, signature):
        '''verify >message< against >signature<'''

        sig = self.keypair.ecdsa_deserialize_compact(b64decode(message.encode("utf-8")))
        return self.keypair.pubkey.ecdsa_verify(sig, signature)
