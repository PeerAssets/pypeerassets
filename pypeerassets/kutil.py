
from hashlib import sha256
from os import urandom
from btcpy.structs.crypto import PublicKey, PrivateKey
from btcpy.structs.transaction import MutableTransaction, TxOut
from btcpy.structs.sig import P2pkhSolver
from btcpy.setup import setup


class Kutil:

    def __init__(self, network: str, privkey: bytearray=None, from_string: str=None,
                 from_wif: str=None) -> None:
        '''
           High level helper class for handling public key cryptography.

           : privkey - privatekey bytes
           : from_wif - <WIF> import private key from your wallet in WIF format
           : from_bytes - import private key in binary format
           : network - specify network [ppc, tppc, btc]
           : from_string - specify seed (string) to make the privkey from
           '''

        self.network = network

        try:
            if self.network.startswith('t') or self.network.endswith('-testnet'):
                setup('testnet')
            else:
                setup('mainnet')
        except ValueError:
            pass

        if privkey is not None:
            self._private_key = PrivateKey(privkey)

        if from_string is not None:
            self._private_key = PrivateKey(sha256(from_string.encode()).digest())

        if from_wif is not None:
            self._private_key = PrivateKey.from_wif(from_wif)

        if not privkey:
            if from_string == from_wif is None:  # generate a new privkey
                self._private_key = PrivateKey(bytearray(urandom(32)))

        self.privkey = str(self._private_key)
        self._public_key = PublicKey.from_priv(self._private_key)
        self.pubkey = str(self._public_key)

    @property
    def address(self) -> str:
        '''generate an address from pubkey'''

        return str(self._public_key.to_address())

    @property
    def wif(self) -> str:
        '''convert raw private key to WIF'''

        return self._private_key.to_wif()

    def sign_transaction(self, txin: TxOut,
                         tx: MutableTransaction) -> MutableTransaction:
        '''sign the parent txn outputs P2PKH'''

        solver = P2pkhSolver(self._private_key)
        return tx.spend([txin], [solver])
