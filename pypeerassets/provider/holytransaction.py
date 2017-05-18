import requests

# https://peercoin.holytransaction.com/info

class Holy:

    '''API wrapper for holytransaction.com blockexplorer,
    it only implements queries relevant to peerassets.
    Please note that holytransactions will only provide last 100k indexed
    transactions for each address.
    '''

    @classmethod
    def __init__(cls, network: str):
        """
        : network = peercoin, peercoin-testnet ...
        """

        cls.net = cls.network_long_to_short(network)
        cls.netname = cls.network_short_to_long(cls.net)
        cls.api = "https://{network}.holytransaction.com/api/".format(network=cls.netname)
        cls.ext_api = "https://{network}.holytransaction.com/ext/".format(network=cls.netname)
        cls.api_methods = ("getdifficulty", "getrawtransaction",
                           "getblockcount", "getblockhash", "getblock")
        cls.ext_api_methods = ("getaddress", "getbalance")
        cls.api_session = requests.Session()

    @property
    def is_testnet(self):
        '''testnet or not?'''

        if self.net == "peercoin":
            return True
        if self.net == "peercoin-testnet":
            return False

    @staticmethod
    def network_long_to_short(name):
        '''convert long network name like "peercoin" to "ppc"'''

        if len(name) < 3:
            if name == "peercoin":
                return "ppc"
            if name == "peercoin-testnet":
                return "tppc"

        return name

    @staticmethod
    def network_short_to_long(name):
        '''convert short network name like "ppc" to "peercoin"'''

        if len(name) > 3:
            if name == "ppc":
                return "peercoin"
            if name == "tppc":
                return "peercoin-testnet"

        return name

    @property
    def network(cls):
        '''which network is this running on?'''

        return cls.net

    @classmethod
    def req(cls, query: str, params: dict):

        if query in cls.api_methods:
            response = cls.api_session.get(cls.api + query, params=params)
        if query in cls.ext_api_methods:
            query = query.join([k+"/"+v+"/" for k,v in params.items()])
            response = cls.api_session.get(cls.ext_api + query)

        return response

    @classmethod
    def getdifficulty(cls) -> dict:
        return cls.req("getdifficulty", {}).json()

    @classmethod
    def getblockcount(cls) -> int:
        return cls.req("getblockcount", {}).content.decode()

    @classmethod
    def getblockhash(cls, blocknum: int) -> str:
        """Returns the hash of the block at ; index 0 is the genesis block."""
        return cls.req("getblockhash", {"index": blocknum}).content.decode()

    @classmethod
    def getblock(cls, hash: str) -> dict:
        """Returns information about the block with the given hash."""
        return cls.req("getblock", {"hash": hash}).json()

    @classmethod
    def getrawtransaction(cls, txid: str, decrypt=1) -> dict:
        """Returns raw transaction representation for given transaction id. decrypt can be set to 0(false) or 1(true)."""

        res = cls.req("getrawtransaction", {"txid": txid, "decrypt": decrypt})
        if decrypt:
            return res.json()
        else:
            return res.content

    @classmethod
    def getaddress(cls, address: str) -> dict:
        """Returns information for given address."""
        return cls.req("getaddress", {"getaddress": address}).json()

    @classmethod
    def getbalance(cls, address: str) -> float:
        """Returns current balance of given address."""
        return cls.req("getbalance", {"getbalance": address}).content.decode()

    @classmethod
    def listtransactions(cls, address: str) -> list:
        """list transactions of this <address>"""

        r = cls.getaddress(address)
        return [i["addresses"] for i in r["last_txs"]]

