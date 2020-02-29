from decimal import Decimal
from http.client import HTTPResponse
import json
from typing import Union, cast
from urllib.request import urlopen

from btcpy.structs.transaction import ScriptSig, Sequence, TxIn

from pypeerassets.exceptions import InsufficientFunds, UnsupportedNetwork
from pypeerassets.provider.common import Provider

'''
TODO:
Add multi-functionality for the endpoints that support it (ex: getblock, getaddress)

'''
class Blockbook(Provider):
    '''API wrapper for https://blockbook.peercoin.net blockexplorer.'''


    def __init__(self, network: str) -> None:
        """
        : network = peercoin [ppc], peercoin-testnet [tppc] ...
        """

        self.net = self._netname(network)['short']
        if 'ppc' not in self.net:
            raise UnsupportedNetwork('This API only supports Peercoin.')

    def api_fetch(self, command: str) -> Union[dict, int, float, str]:

        apiurl = 'https://blockbook.peercoin.net/api/'
        if self.is_testnet:
            apiurl = 'https://tblockbook.peercoin.net/api/'

        response = cast(HTTPResponse, urlopen(apiurl + command))
        if response.status != 200:
            raise Exception(response.reason)

        r = response.read()

        try:
            return json.loads(r.decode())
        except json.decoder.JSONDecodeError:
            return r.decode()

    def getdifficulty(self) -> dict:
        '''Returns the current difficulty.'''

        return cast(dict, self.api_fetch(''))['backend']['difficulty']

    def getblockcount(self) -> int:
        '''Returns the current block index.'''

        return cast(int, self.api_fetch(''))['backend']['blocks']

    def getblockhash(self, index: int) -> str:
        '''Returns the hash of the block at ; index 0 is the genesis block.'''

        return cast(str, self.api_fetch('block-index/' + str(index))['blockHash'])

    def getblock(self, hash: str) -> dict:
        '''Returns information about the block with the given hash.'''

        return cast(dict, self.api_fetch('block/' + hash))

    def getrawtransaction(self, txid: str, decrypt: int=0) -> dict:
        '''Returns raw transaction representation for given transaction id.
        decrypt can be set to 0(false) or 1(true).'''

        q = '/tx-specific/{txid}'.format(txid=txid)

        return cast(dict, self.api_fetch(q))

    def getaddress(self, address: str) -> dict:
        '''Returns information for given address.'''

        return cast(dict, self.api_fetch('address/' + address))

    def listunspent(self, address: str) -> list:
        '''Returns unspent transactions for given address.'''

        try:
            return cast(dict, self.api_fetch('utxo/' + address))
        except KeyError:
            raise InsufficientFunds('Insufficient funds.')

    def select_inputs(self, address: str, amount: int) -> dict:

        utxos = []
        utxo_sum = Decimal(-0.01)  # starts from negative due to minimal fee
        for tx in self.listunspent(address=address):
                script = self.getrawtransaction(tx['txid'])['vout'][0]['scriptPubKey']['hex']
                utxos.append(
                    TxIn(txid=tx['txid'],
                         txout=tx['vout'],
                         sequence=Sequence.max(),
                         script_sig=ScriptSig.unhexlify(script))
                         )

                utxo_sum += Decimal(tx['amount'])
                if utxo_sum >= amount:
                    return {'utxos': utxos, 'total': utxo_sum}

        if utxo_sum < amount:
            raise InsufficientFunds('Insufficient funds.')

        raise Exception("undefined behavior :.(")

    def getbalance(self, address: str) -> Decimal:
        '''Returns current balance of given address.'''

        try:
            return Decimal(cast(float, self.api_fetch('address/' + address))['balance'])
        except TypeError:
            return Decimal(0)

    def getreceivedbyaddress(self, address: str) -> Decimal:

        return Decimal(cast(float, self.getaddress(address)['totalReceived']))

    def listtransactions(self, address: str) -> list:

        try:
            r = self.getaddress(address)['transactions']
            return [i for i in r]
        except KeyError:
            return None
