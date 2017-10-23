from hashlib import sha256
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
            setup(self.network)
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

    @property
    def address(self) -> str:
        '''generate an address from pubkey'''

        return str(PublicKey.from_priv(self._private_key).to_address())

    def sign_transaction(self, txin: TxOut,
                         tx: MutableTransaction) -> MutableTransaction:
        '''sign the parent txn outputs P2PKH'''

        solver = P2pkhSolver(self._private_key)
        return tx.spend([txin], [solver])
