import requests


class Cryptoid:

    '''API wrapper for http://chainz.cryptoid.info blockexplorer.'''

    @classmethod
    def __init__(self, network: str):
        """
        : network = ppc, tppc ...
        """

        self.net = network
        self.api_session = requests.Session()

    key = '7547f94398e3'
    private = ('getbalance', 'unspent')

    @classmethod
    def req(self, query: str):

        addr = 'https://chainz.cryptoid.info/{0}/api.dws'.format(self.net)
        query = addr + "?q=" + query
        if (p in self.private for p in query):
            query += "&key=" + self.key
        response = self.api_session.get(query)

        assert response.status_code == 200, {'error': 'API error: ' + str(response.status_code)}
        return response.json()

    @classmethod
    def getblockcount(cls) -> int:

        return cls.req('getblockcount')

    @classmethod
    def getdifficulty(cls) -> float:

        return cls.req('getdifficulty')

    def getbalance(cls, address: str) -> float:

        return float(cls.req('getbalance' + "&a=" + address))

    def getreceivedbyaddress(cls, address: str) -> float:

        return float(cls.req('getreceivedbyaddress' + "&a=" + address))

    def listunspent(cls, address: str) -> list:

        return cls.req('unspent' + "&a=" + address)['unspent_outputs']
