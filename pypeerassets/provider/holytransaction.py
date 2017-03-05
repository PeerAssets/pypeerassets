import requests

# https://peercoin.holytransaction.com/info

class Holy:

    '''API wrapper for holytransaction.com blockexplorer,
    it only implements queries relevant to peerassets.
    '''

    @classmethod
    def __init__(cls, network: str):
        """
        : network = peercoin, peercoin-testnet ...
        """

        cls.net = network
        cls.api = "https://{network}.holytransaction.com/api/".format(network=cls.net)
        cls.ext_api = "https://{network}.holytransaction.com/ext/".format(network=cls.net)
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

    @property
    def network(self):
        '''which network is this running on?'''

        if self.net == "peercoin":
            return "ppc"
        if self.net == "peercoin-testnet":
            return "tppc"


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
        return cls.req("getrawtransaction", {"txid": txid, "decrypt": decrypt}).json()

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
        return [i["addresses"] for i in r["last_txs"] if i["type"] == "vin"]

