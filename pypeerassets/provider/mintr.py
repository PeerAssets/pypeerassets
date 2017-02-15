import requests

class Mintr:

    '''API wrapper for mintr.org blockexplorer,
    it only implements queries relevant to peerassets.
    This wrapper does some tweaks to output to match original RPC response.'''

    @classmethod
    def __init__(cls, network="peercoin"):

        cls.net = network
        cls.api = "https://{0}.mintr.org/api/".format(cls.net)

    @property
    def is_testnet(self):
        '''testnet or not?'''
        return False

    @property
    def network(self):
        '''which network is this running on?'''

        if self.network == "peercoin":
            return "ppc"

    @classmethod
    def get(cls, query):

        requests.packages.urllib3.disable_warnings()
        return requests.get(cls.api + query, verify=False).json()

    @classmethod
    def getinfo(cls):
        '''mock response, to allow compatibility with local rpc node'''

        return {"testnet": False}

    @classmethod
    def getrawtransaction(cls, txid, verbose=1):
        '''this mimics the behaviour of local node `getrawtransaction` query with argument 1'''

        def wrapper(raw):
            '''make Mintr API response just like RPC response'''

            raw["blocktime"] = raw["time"]
            raw.pop("time")

            for v in raw["vout"]:
                v["scriptPubKey"] = {"asm": v["asm"], "hex": v["hex"],
                                     "type": v["type"], "reqSigs": v["reqsigs"],
                                     "address": [v["address"]]
                                    }
                for k in ("address", "asm", "hex", "reqsigs", "type"):
                    v.pop(k)

            return raw

        if verbose == 0:
            return cls.get("tx/hash/" + txid)
        else:
            resp = cls.get("tx/hash/" + txid + "/full")
            if not resp == {'error': 'Unknown API call'}:
                return wrapper(resp)

    @classmethod
    def listtransactions(cls, addr):
        '''get information about <address>'''

        response = cls.get("address/balance/" + addr + "/full")
        assert response != {'error': 'Could not decode hash'}, {"error": "Can not find the address."}

        txid = []
        for i in response["transactions"]:
            t = {"confirmations": i["confirmations"],
                 "time": i["time"],
                 "txid": i["tx_hash"],
                 "address": response["address"]
                }
            if i["sent"] == "":
                t["amount"] = i["received"]
                t["category"] = "send"
            else:
                t["amount"] = i["sent"]
                t["category"] = "receive"

            txid.append(t)

        return txid

