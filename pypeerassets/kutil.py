from hashlib import sha256
from btcpy.structs.crypto import PublicKey, PrivateKey


class Kutil:

    def __init__(self, network: str, privkey: bytes=None, seed: str=None,
                 wif: str=None) -> None:
        ''': wif - <WIF> import private key from your wallet in WIF format
           : privkey - <privkey> import private key in binary format
           : network - specify network [ppc, tppc, btc]
           : seed - specify seed (string) to make the privkey from'''

        self.network = network

        if privkey is not None:
            self._private_key = PrivateKey(privkey)

        if seed is not None:
            self._private_key = PrivateKey(sha256(seed.encode()).digest())

        if wif is not None:
            self._private_key = PrivateKey.from_wif(wif)
            #self._wif_prefix = key['net_prefix']

        self.privkey = self._private_key.hexlify()
        self.pubkey = PublicKey.from_priv(self._private_key).hexlify()

    @property
    def address(self) -> str:
        '''generate an address from pubkey'''

        return str(PublicKey.from_priv(self._private_key).to_address(self.network))
