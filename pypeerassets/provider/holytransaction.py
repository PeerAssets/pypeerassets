
'''
API wrapper for holytransaction blockexplorer.
See https://peercoin.holytransaction.com/info for more information.
'''

import requests
from decimal import Decimal
from .common import Provider


class Holy(Provider):

    """API wrapper for holytransaction.com blockexplorer,
    it only implements queries relevant to peerassets.
    Please note that holytransactions will only provide last 100k indexed
    transactions for each address.
    """

    def __init__(self, network: str):
        """
        : network = ppc, peercoin-testnet ...
        """

        self.net = self._netname(network)['long']
        self.api = "https://{network}.holytransaction.com/api/".format(
                   network=self._netname(network)['long'])
        self.ext_api = "https://{network}.holytransaction.com/ext/".format(
                       network=self._netname(network)['long'])
        self.api_methods = ("getdifficulty", "getrawtransaction",
                           "getblockcount", "getblockhash", "getblock")
        self.ext_api_methods = ("getaddress", "getbalance")
        self.api_session = requests.Session()

    def req(self, query: str, params: dict):
        """Send request, return response."""

        if query in self.api_methods:
            response = self.api_session.get(self.api + query, params=params)
        if query in self.ext_api_methods:
            query = query.join([k+"/"+v+"/" for k,v in params.items()])
            response = self.api_session.get(self.ext_api + query)

        return response

    def getdifficulty(self) -> dict:
        """Returns current difficulty."""
        return self.req("getdifficulty", {}).json()

    def getblockcount(self) -> int:
        """Returns block count."""
        return int(self.req("getblockcount", {}).content.decode())

    def getblockhash(self, blocknum: int) -> str:
        """Returns the hash of the block at ; index 0 is the genesis block."""
        return self.req("getblockhash", {"index": blocknum}).content.decode()

    def getblock(self, hash: str) -> dict:
        """Returns information about the block with the given hash."""
        return self.req("getblock", {"hash": hash}).json()

    @classmethod
    def getrawtransaction(self, txid: str, decrypt=1) -> dict:
        """Returns raw transaction representation for given transaction id.
        decrypt can be set to 0(false) or 1(true)."""

        res = self.req("getrawtransaction", {"txid": txid, "decrypt": decrypt})

        if decrypt:
            return res.json()
        else:
            return res.content

    def getaddress(self, address: str) -> dict:
        """Returns information for given address."""
        return self.req("getaddress", {"getaddress": address}).json()

    def getbalance(self, address: str) -> Decimal:
        """Returns current balance of given address."""

        return Decimal(self.req("getbalance", {"getbalance": address}).content.decode())

    def listtransactions(self, address: str) -> list:
        """list transactions of this <address>"""

        r = self.getaddress(address)
        try:
            return [i["addresses"] for i in r["last_txs"]]
        except KeyError:
            print({'error': 'Address not found.'})
