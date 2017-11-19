
from pypeerassets.networks import net_query
from pypeerassets.base58 import b58encode, b58decode
from hashlib import sha256, new
from binascii import unhexlify, hexlify
from os import urandom
from btcpy.structs.crypto import PublicKey, PrivateKey
from btcpy.structs.transaction import MutableTransaction, TxOut
from btcpy.structs.sig import P2pkhSolver
from btcpy.setup import setup


class Kutil:

    def __init__(self, network: str, privkey: bytes=None, seed: str=None,
                 wif: str=None) -> None:
        '''
           High level helper class for handling public key cryptography.

           : wif - <WIF> import private key from your wallet in WIF format
           : privkey - <privkey> import private key in binary format
           : network - specify network [ppc, tppc, btc]
           : seed - specify seed (string) to make the privkey from'''

        self.network = network

        try:
            if self.network.startswith('t'):
                setup('testnet')
            else:
                setup('mainnet')
        except ValueError:
            pass

        if privkey is not None:
            self._private_key = PrivateKey(privkey)

        if seed is not None:
            self._private_key = PrivateKey(sha256(seed.encode()).digest())

        if wif is not None:
            self._private_key = PrivateKey.from_wif(wif)
            #self._wif_prefix = key['net_prefix']

        if privkey == seed == wif is None:  # generate a new privkey
            self._private_key = PrivateKey(bytearray(urandom(32)))

        self.privkey = self._private_key.hexlify()
        self.pubkey = PublicKey.from_priv(self._private_key).hexlify()
        self.load_network_parameters(network)

    def load_network_parameters(self, network: str) -> None:
        '''loads network parameters and sets class variables'''

        for field, var in zip(net_query(network)._fields, net_query(network)):
            setattr(self, field, var)

    def wif_to_privkey(self, wif: str) -> dict:
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

        extkey = unhexlify(self.wif_prefix + self.privkey.encode() + b'01')  # compressed by default
        extcheck = extkey + sha256(sha256(extkey).digest()).digest()[0:4]
        wif = b58encode(extcheck)

        return wif

    def sign_transaction(self, txin: TxOut,
                         tx: MutableTransaction) -> MutableTransaction:
        '''sign the parent txn outputs P2PKH'''

        solver = P2pkhSolver(self._private_key)
        return tx.spend([txin], [solver])
