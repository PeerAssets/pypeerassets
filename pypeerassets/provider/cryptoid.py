import requests
from .common import Provider


class Cryptoid(Provider):

    '''API wrapper for http://chainz.cryptoid.info blockexplorer.'''

    @classmethod
    def __init__(self, network: str):
        """
        : network = peercoin [ppc], peercoin-testnet [tppc] ...
        """

        self.net = self._netname(network)['short']

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

    @classmethod
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

    @classmethod
    def block_req(self, query: str) -> dict:

        response = self.api_session.get(query)
        assert response.status_code == 200, {'error': 'API error: ' + str(response.status_code)}
        return response.json()

    @classmethod
    def getblockcount(cls) -> int:

        return cls.api_req('getblockcount')

    @classmethod
    def getblock(cls, blockhash: str) -> dict:
        '''query block using <blockhash> as key.'''

        query = cls.block_url(cls.net) + '&hash={blockhash}'.format(net=cls.net,
                                                                    blockhash=blockhash)
        return cls.block_req(query)

    @classmethod
    def getblockhash(cls, blocknum: int) -> str:
        '''get blockhash'''

        return cls.api_req('getblockhash' + '&height=' + str(blocknum))

    @classmethod
    def getdifficulty(cls) -> float:

        return cls.api_req('getdifficulty')

    @classmethod
    def getbalance(cls, address: str) -> float:

        return float(cls.api_req('getbalance' + "&a=" + address))

    @classmethod
    def getreceivedbyaddress(cls, address: str) -> float:

        return float(cls.api_req('getreceivedbyaddress' + "&a=" + address))

    @classmethod
    def listunspent(cls, address: str) -> list:

        return cls.api_req('unspent' + "&active=" + address)['unspent_outputs']

    @classmethod
    def getrawtransaction(cls, txid: str) -> dict:

        query = cls.explorer_url + 'tx.raw.dws?coin={net}&id={txid}'.format(net=cls.format_name(cls.net),
                                                                            txid=txid)
        return cls.block_req(query)

    @classmethod
    def listtransactions(cls, address: str) -> list:

        query = cls.explorer_url + 'address.summary.dws?coin={net}&id={addr}'.format(net=cls.format_name(cls.net),
                                                                                     addr=address)
        resp = cls.block_req(query)
        return [i[1].lower() for i in resp['tx']]
