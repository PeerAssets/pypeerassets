import requests

class Mintr:

    '''API wrapper for mintr.org blockexplorer,
    it only implements queries relevant to peerassets.
    This wrapper does some tweaks to output to match original RPC response.'''

    @classmethod
    def __init__(cls, network):

        cls.api = "https://{0}.mintr.org/api/".format(network)

    @classmethod
    def get(cls, query):

        requests.packages.urllib3.disable_warnings()
        return requests.get(cls.api + query, verify=False).json()

    @classmethod
    def getrawtransaction(cls, txid):
        '''this mimics the behaviour of local node `getrawtransaction` query with argument 1'''

        return cls.get("tx/hash/" + txid)

    @classmethod
    def listtransactions(cls, addr):
        '''get information about <address>'''

        response = cls.get("address/balance/" + addr + "/full")
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

