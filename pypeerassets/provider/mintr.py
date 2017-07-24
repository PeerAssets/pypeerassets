import requests


class Mintr:

    '''API wrapper for mintr.org blockexplorer,
    it only implements queries relevant to peerassets.
    This wrapper does some tweaks to output to match original RPC response.'''

    @classmethod
    def __init__(cls):

        cls.api = "https://peercoin.mintr.org/api/"

    @property
    def is_testnet(self):
        '''testnet or not?'''
        return False

    @property
    def network(self):
        '''which network is this running on?'''
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
                                     "addresses": [v["address"]]
                                    }
                for k in ("address", "asm", "hex", "reqsigs", "type"):
                    v.pop(k)

            for i in raw["vin"]:
                i["txid"] = i["output_txid"]
                i["addresses"] = i["address"]
                i["vout"] = int(i["vout"])
                i.pop("output_txid")
                i.pop("address")

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

    @classmethod
    def getblock(cls, blockhash: str) -> dict:
        '''get full block data, query by <blockhash>'''

        def _wrapper(raw):

            raw["tx"] = []

            for t in raw["transactions"]:
                raw["tx"].append(t["tx_hash"])

            raw["height"] = int(raw["height"])
            raw.pop("transactions")

            return raw

        resp = cls.get("block/height/" + blockhash + "/full")

        if resp != {'error': 'Could not decode hash'}:
            return _wrapper(resp)
        else:
            return resp
