import json
from json import JSONDecodeError
from urllib.request import urlopen
from .common import Provider
from decimal import Decimal, getcontext
from pypeerassets.exceptions import InsufficientFunds
from btcpy.structs.transaction import TxIn, Sequence, ScriptSig
from pypeerassets.exceptions import UnsupportedNetwork


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

    def api_fetch(self, command):

        apiurl = 'https://explorer.peercoin.net/api/'
        if self.is_testnet:
            apiurl = 'https://testnet-explorer.peercoin.net/api/'

        query = urlopen(apiurl + command).read()

        try:
            return json.loads(query)
        except JSONDecodeError:
            return query.decode()

    def ext_fetch(self, command):

        extapiurl = 'https://explorer.peercoin.net/ext/'
        if self.is_testnet:
            extapiurl = 'https://testnet-explorer.peercoin.net/ext/'

        query = urlopen(extapiurl + command).read()

        try:
            return json.loads(query)
        except JSONDecodeError:
            return query.decode()

    def getdifficulty(self) -> dict:
        '''Returns the current difficulty.'''

        return self.api_fetch('getdifficulty')

    def getconnectioncount(self) -> int:
        '''Returns the number of connections the block explorer has to other nodes.'''

        return self.api_fetch('getconnectioncount')

    def getblockcount(self) -> int:
        '''Returns the current block index.'''

        return self.api_fetch('getblockcount')

    def getblockhash(self, index: int) -> str:
        '''Returns the hash of the block at ; index 0 is the genesis block.'''

        return self.api_fetch('getblockhash?index=' + str(index))

    def getblock(self, hash: str) -> dict:
        '''Returns information about the block with the given hash.'''

        return self.api_fetch('getblock?hash=' + hash)

    def getrawtransaction(self, txid: str, decrypt=1) -> dict:
        '''Returns raw transaction representation for given transaction id.
        decrypt can be set to 0(false) or 1(true).'''

        q = 'getrawtransaction?txid={txid}&decrypt={decrypt}'.format(txid=txid, decrypt=decrypt)

        return self.api_fetch(q)

    def getnetworkghps(self) -> float:
        '''Returns the current network hashrate. (ghash/s)'''

        return self.api_fetch('getnetworkghps')

    def getmoneysupply(self) -> Decimal:
        '''Returns current money supply.'''

        return Decimal(self.ext_fetch('getmoneysupply'))

    def getdistribution(self) -> dict:
        '''Returns wealth distribution stats.'''

        return self.ext_fetch('getdistribution')

    def getaddress(self, address: str) -> dict:
        '''Returns information for given address.'''

        return self.ext_fetch('getaddress/' + address)

    def listunspent(self, address: str) -> list:
        '''Returns unspent transactions for given address.'''

        return self.ext_fetch('listunspent/' + address)['unspent_outputs']

    def select_inputs(self, address, amount):
        raise NotImplementedError

    def txinfo(self, txid: str) -> dict:
        '''Returns information about given transaction.'''

        return self.ext_fetch('txinfo/' + txid)

    def getbalance(self, address: str) -> Decimal:
        '''Returns current balance of given address.'''

        return Decimal(self.ext_fetch('getbalance/' + address))

    def getreceivedbyaddress(self, address: str) -> Decimal:

        return Decimal(self.getaddress(address)['received'])

    def listtransactions(self, address: str) -> list:

        r = self.getaddress(address)['last_txs']

        return [i['addresses'] for i in r]
