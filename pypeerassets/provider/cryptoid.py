import requests
from operator import itemgetter
from .common import Provider
from decimal import Decimal, getcontext
from pypeerassets.exceptions import InsufficientFunds
from btcpy.structs.transaction import TxIn, Sequence, ScriptSig


class Cryptoid(Provider):

    '''API wrapper for http://chainz.cryptoid.info blockexplorer.'''

    def __init__(self, network: str) -> None:
        """
        : network = peercoin [ppc], peercoin-testnet [tppc] ...
        """

        self.net = self._netname(network)['short']
        if 'ppc' in self.net:
            getcontext().prec = 6  # set to six decimals if it's Peercoin

    key = '7547f94398e3'
    api_calls = ('getblockcount', 'getdifficulty', 'getbalance',
                 'getreceivedbyaddress', 'listunspent')
    private = ('getbalance', 'unspent')
    explorer_url = 'https://chainz.cryptoid.info/explorer/'
    api_session = requests.Session()

    @staticmethod
    def format_name(net: str) -> str:
        '''take care of specifics of cryptoid naming system'''

        if net.startswith('t') or 'testnet' in net:
            net = net[1:] + '-test'
        else:
            net = net

        return net

    def api_req(self, query: str) -> dict:

        api_url = 'https://chainz.cryptoid.info/{net}/api.dws'.format(
                                                               net=self.format_name(self.net))

        if (p in self.api_calls for p in query):
            query = api_url + "?q=" + query

            if (p in self.private for p in query):
                query += "&key=" + self.key

            response = self.api_session.get(query)

        assert response.status_code == 200, {'error': 'API error: ' + str(response.status_code)}
        return response.json()

    def block_req(self, query: str) -> dict:

        response = self.api_session.get(query)
        assert response.status_code == 200, {'error': 'API error: ' + str(response.status_code)}
        return response.json()

    def getblockcount(self) -> int:

        return self.api_req('getblockcount')

    def getblock(self, blockhash: str) -> dict:
        '''query block using <blockhash> as key.'''

        query = self.explorer_url + 'block.raw.dws?coin={net}&hash={blockhash}'.format(net=self.format_name(self.net),
                                                                                       blockhash=blockhash)
        return self.block_req(query)

    def getblockhash(self, blocknum: int) -> str:
        '''get blockhash'''

        return self.api_req('getblockhash' + '&height=' + str(blocknum))

    def getdifficulty(self) -> float:

        return self.api_req('getdifficulty')

    def getbalance(self, address: str) -> Decimal:

        return Decimal(self.api_req('getbalance' + "&a=" + address))

    def getreceivedbyaddress(self, address: str) -> Decimal:

        return Decimal(self.api_req('getreceivedbyaddress' + "&a=" + address))

    def listunspent(self, address: str) -> list:

        return self.api_req('unspent' + "&active=" + address)['unspent_outputs']

    def select_inputs(self, address: str, amount: int):
        '''select UTXOs'''

        utxos = []
        utxo_sum = Decimal(-0.01)  # starts from negative due to minimal fee
        for tx in sorted(self.listunspent(address=address), key=itemgetter('confirmations')):

                utxos.append(
                    TxIn(txid=tx['tx_hash'],
                         txout=tx['tx_ouput_n'],
                         sequence=Sequence.max(),
                         script_sig=ScriptSig.empty())
                         )

                utxo_sum += Decimal(int(tx['value']) / 100000000)
                if utxo_sum >= amount:
                    return {'utxos': utxos, 'total': utxo_sum}

        if utxo_sum < amount:
            raise InsufficientFunds('Insufficient funds.')

    def getrawtransaction(self, txid: str, decrypt=1) -> dict:

        query = self.explorer_url + 'tx.raw.dws?coin={net}&id={txid}'.format(net=self.format_name(self.net),
                                                                             txid=txid)
        if not decrypt:
            query += '&hex'
            return self.block_req(query)['hex']

        return self.block_req(query)

    def listtransactions(self, address: str) -> list:

        query = self.explorer_url + 'address.summary.dws?coin={net}&id={addr}'.format(net=self.format_name(self.net),
                                                                                      addr=address)
        resp = self.block_req(query)
        if resp:
            return [i[1].lower() for i in resp['tx']]
        else:
            return None
