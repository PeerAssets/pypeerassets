from decimal import Decimal, getcontext
from http.client import HTTPResponse
import json
from typing import Union, cast
from urllib.request import urlopen

from btcpy.structs.transaction import ScriptSig, Sequence, TxIn

from pypeerassets.exceptions import InsufficientFunds, UnsupportedNetwork
from pypeerassets.provider.common import Provider


class Explorer(Provider):

    '''API wrapper for https://explorer.peercoin.net blockexplorer.'''

    def __init__(self, network: str) -> None:
        """
        : network = peercoin [ppc], peercoin-testnet [tppc] ...
        """

        self.net = self._netname(network)['short']
        if 'ppc' not in self.net:
            raise UnsupportedNetwork('This API only supports Peercoin.')
            getcontext().prec = 6  # set to six decimals if it's Peercoin

    def api_fetch(self, command: str) -> Union[dict, int, float, str]:

        apiurl = 'https://explorer.peercoin.net/api/'
        if self.is_testnet:
            apiurl = 'https://testnet-explorer.peercoin.net/api/'

        response = cast(HTTPResponse, urlopen(apiurl + command))
        if response.status != 200:
            raise Exception(response.reason)

        r = response.read()

        try:
            return json.loads(r.decode())
        except json.decoder.JSONDecodeError:
            return r.decode()

    def ext_fetch(self, command: str) -> Union[dict, int, float, str]:

        extapiurl = 'https://explorer.peercoin.net/ext/'
        if self.is_testnet:
            extapiurl = 'https://testnet-explorer.peercoin.net/ext/'

        response = cast(HTTPResponse, urlopen(extapiurl + command))
        if response.status != 200:
            raise Exception(response.reason)

        try:
            return json.loads(response.read().decode())
        except json.decoder.JSONDecodeError:
            return response.read().decode()

    def getdifficulty(self) -> dict:
        '''Returns the current difficulty.'''

        return cast(dict, self.api_fetch('getdifficulty'))

    def getconnectioncount(self) -> int:
        '''Returns the number of connections the block explorer has to other nodes.'''

        return cast(int, self.api_fetch('getconnectioncount'))

    def getblockcount(self) -> int:
        '''Returns the current block index.'''

        return cast(int, self.api_fetch('getblockcount'))

    def getblockhash(self, index: int) -> str:
        '''Returns the hash of the block at ; index 0 is the genesis block.'''

        return cast(str, self.api_fetch('getblockhash?index=' + str(index)))

    def getblock(self, hash: str) -> dict:
        '''Returns information about the block with the given hash.'''

        return cast(dict, self.api_fetch('getblock?hash=' + hash))

    def getrawtransaction(self, txid: str, decrypt: int=0) -> dict:
        '''Returns raw transaction representation for given transaction id.
        decrypt can be set to 0(false) or 1(true).'''

        q = 'getrawtransaction?txid={txid}&decrypt={decrypt}'.format(txid=txid, decrypt=decrypt)

        return cast(dict, self.api_fetch(q))

    def getnetworkghps(self) -> float:
        '''Returns the current network hashrate. (ghash/s)'''

        return cast(float, self.api_fetch('getnetworkghps'))

    def getmoneysupply(self) -> Decimal:
        '''Returns current money supply.'''

        return Decimal(cast(float, self.ext_fetch('getmoneysupply')))

    def getdistribution(self) -> dict:
        '''Returns wealth distribution stats.'''

        return cast(dict, self.ext_fetch('getdistribution'))

    def getaddress(self, address: str) -> dict:
        '''Returns information for given address.'''

        return cast(dict, self.ext_fetch('getaddress/' + address))

    def listunspent(self, address: str) -> list:
        '''Returns unspent transactions for given address.'''

        try:
            return cast(dict, self.ext_fetch('listunspent/' + address))['unspent_outputs']
        except KeyError:
            raise InsufficientFunds('Insufficient funds.')

    def select_inputs(self, address: str, amount: int) -> dict:

        utxos = []
        utxo_sum = Decimal(-0.01)  # starts from negative due to minimal fee
        for tx in self.listunspent(address=address):

                utxos.append(
                    TxIn(txid=tx['tx_hash'],
                         txout=tx['tx_ouput_n'],
                         sequence=Sequence.max(),
                         script_sig=ScriptSig.unhexlify(tx['script']))
                         )

                utxo_sum += Decimal(tx['value'] / 10**8)
                if utxo_sum >= amount:
                    return {'utxos': utxos, 'total': utxo_sum}

        if utxo_sum < amount:
            raise InsufficientFunds('Insufficient funds.')

        raise Exception("undefined behavior :.(")

    def txinfo(self, txid: str) -> dict:
        '''Returns information about given transaction.'''

        return cast(dict, self.ext_fetch('txinfo/' + txid))

    def getbalance(self, address: str) -> Decimal:
        '''Returns current balance of given address.'''

        try:
            return Decimal(cast(float, self.ext_fetch('getbalance/' + address)))
        except TypeError:
            return Decimal(0)

    def getreceivedbyaddress(self, address: str) -> Decimal:

        return Decimal(cast(float, self.getaddress(address)['received']))

    def listtransactions(self, address: str) -> list:

        try:
            r = self.getaddress(address)['last_txs']
            return [i['addresses'] for i in r]
        except KeyError:
            return None
