from decimal import Decimal, getcontext
import json
from operator import itemgetter
from urllib.request import Request, urlopen

from btcpy.structs.transaction import TxIn, Sequence, ScriptSig

from pypeerassets.exceptions import InsufficientFunds
from pypeerassets.provider.common import Provider


class Cryptoid(Provider):

    '''API wrapper for http://chainz.cryptoid.info blockexplorer.'''

    api_key = '7547f94398e3'
    api_url_fmt = 'https://chainz.cryptoid.info/{net}/api.dws'
    explorer_url = 'https://chainz.cryptoid.info/explorer/'

    def __init__(self, network: str) -> None:
        """
        : network = peercoin [ppc], peercoin-testnet [tppc] ...
        """

        self.net = self._netname(network)['short']
        self.api_url = self.api_url_fmt.format(net=self.format_name(self.net))
        if 'ppc' in self.net:
            getcontext().prec = 6  # set to six decimals if it's Peercoin


    @staticmethod
    def format_name(net: str) -> str:
        '''take care of specifics of cryptoid naming system'''

        if net.startswith('t') or 'testnet' in net:
            net = net[1:] + '-test'
        else:
            net = net

        return net

    @staticmethod
    def get_url(url: str) -> dict:
        '''Perform a GET request for the url and return a dictionary parsed from
        the JSON response.'''

        request = Request(url, headers={"User-Agent": "pypeerassets"})
        response = urlopen(request)
        if response.getcode() != 200:
            raise Exception(response.reason)
        return json.loads(response.read().decode())

    def api_req(self, query: str) -> dict:

        url = self.api_url + "?q=" + query + "&key=" + self.api_key
        return self.get_url(url)

    def getblockcount(self) -> int:

        return self.api_req('getblockcount')

    def getblock(self, blockhash: str) -> dict:
        '''query block using <blockhash> as key.'''

        query = self.explorer_url + 'block.raw.dws?coin={net}&hash={blockhash}'.format(net=self.format_name(self.net),
                                                                                       blockhash=blockhash)
        return self.get_url(query)

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

    def select_inputs(self, address: str, amount: int) -> dict:
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
            return self.get_url(query)['hex']

        return self.get_url(query)

    def listtransactions(self, address: str) -> list:

        query = self.explorer_url + 'address.summary.dws?coin={net}&id={addr}'.format(net=self.format_name(self.net),
                                                                                      addr=address)
        resp = self.get_url(query)
        if resp:
            return [i[1].lower() for i in resp['tx']]
        else:
            return None
