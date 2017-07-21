
'''
API wrapper for holytransaction blockexplorer.
See https://peercoin.holytransaction.com/info for more information.
'''

import requests


class Holy:

    """API wrapper for holytransaction.com blockexplorer,
    it only implements queries relevant to peerassets.
    Please note that holytransactions will only provide last 100k indexed
    transactions for each address.
    """

    @classmethod
    def __init__(self, network: str):
        """
        : network = peercoin, peercoin-testnet ...
        """

        self.net = self.network_long_to_short(network)
        self.netname = self.network_short_to_long(self.net)
        self.api = "https://{network}.holytransaction.com/api/".format(network=self.netname)
        self.ext_api = "https://{network}.holytransaction.com/ext/".format(network=self.netname)
        self.api_methods = ("getdifficulty", "getrawtransaction",
                           "getblockcount", "getblockhash", "getblock")
        self.ext_api_methods = ("getaddress", "getbalance")
        self.api_session = requests.Session()

    @property
    def is_testnet(self):
        """testnet or not?"""

        if self.net == "peercoin":
            return False
        if self.net == "peercoin-testnet":
            return True

    @staticmethod
    def network_long_to_short(name):
        """convert long network name like "peercoin" to "ppc"."""

        if len(name) < 3:
            if name == "peercoin":
                return "ppc"
            if name == "peercoin-testnet":
                return "tppc"

        return name

    @staticmethod
    def network_short_to_long(name):
        """convert short network name like "ppc" to "peercoin". """

        if len(name) > 3:
            if name == "ppc":
                return "peercoin"
            if name == "tppc":
                return "peercoin-testnet"

        return name

    @property
    def network(self):
        """which network is this running on?"""
        return self.net

    @classmethod
    def req(self, query: str, params: dict):
        """Send request, return response."""
        if query in self.api_methods:
            response = self.api_session.get(self.api + query, params=params)
        if query in self.ext_api_methods:
            query = query.join([k+"/"+v+"/" for k,v in params.items()])
            response = self.api_session.get(self.ext_api + query)

        return response

    @classmethod
    def getdifficulty(self) -> dict:
        """Returns current difficulty."""
        return self.req("getdifficulty", {}).json()

    @classmethod
    def getblockcount(self) -> int:
        """Returns block count."""
        return self.req("getblockcount", {}).content.decode()

    @classmethod
    def getblockhash(self, blocknum: int) -> str:
        """Returns the hash of the block at ; index 0 is the genesis block."""
        return self.req("getblockhash", {"index": blocknum}).content.decode()

    @classmethod
    def getblock(self, hash: str) -> dict:
        """Returns information about the block with the given hash."""
        return self.req("getblock", {"hash": hash}).json()

    @classmethod
    def getrawtransaction(self, txid: str, decrypt=1) -> dict:
        """Returns raw transaction representation for given transaction id. decrypt can be set to 0(false) or 1(true)."""
        res = self.req("getrawtransaction", {"txid": txid, "decrypt": decrypt})

        if decrypt:
            return res.json()
        else:
            return res.content

    @classmethod
    def getaddress(self, address: str) -> dict:
        """Returns information for given address."""
        return self.req("getaddress", {"getaddress": address}).json()

    @classmethod
    def getbalance(self, address: str) -> float:
        """Returns current balance of given address."""
        return self.req("getbalance", {"getbalance": address}).content.decode()

    @classmethod
    def listtransactions(self, address: str) -> list:
        """list transactions of this <address>"""
        r = self.getaddress(address)
        return [i["addresses"] for i in r["last_txs"]]
