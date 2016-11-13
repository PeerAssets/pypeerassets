
'''Communicate with local or remote peercoin-daemon via JSON-RPC'''

from operator import itemgetter

try:
    from peercoin_rpc import Client
except:
    raise EnvironmentError("peercoin_rpc library is required for this to work,\
                            use pip to install it.")

def select_inputs(cls, total_amount):
    '''finds apropriate utxo's to include in rawtx, while being careful
    to never spend old transactions with a lot of coin age.
    Argument is intiger, returns list of apropriate UTXO's'''

    utxo = []
    utxo_sum = float(-0.01) ## starts from negative due to minimal fee
    for tx in sorted(cls.listunspent(), key=itemgetter('confirmations')):

        utxo.append({
            "txid": tx["txid"],
            "vout": tx["vout"],
            "scriptSig": tx["scriptPubKey"]
        })

        utxo_sum += float(tx["amount"])
        if utxo_sum >= total_amount:
            return utxo

    if utxo_sum < total_amount:
        raise ValueError("Not enough funds.")

class RpcNode(Client):

    select_inputs = select_inputs

