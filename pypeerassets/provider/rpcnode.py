
'''Communicate with local or remote peercoin-daemon via JSON-RPC'''

from operator import itemgetter
from .common import Provider
from pypeerassets.exceptions import InsufficientFunds
from pypeerassets.pa_constants import param_query
from btcpy.structs.transaction import MutableTxIn, Sequence, ScriptSig
from decimal import Decimal, getcontext
getcontext().prec = 6

try:
    from peercoin_rpc import Client
except:
    raise EnvironmentError("peercoin_rpc library is required for this to work,\
                            use pip to install it.")


class RpcNode(Client, Provider):
    '''JSON-RPC connection to local Peercoin node'''

    def select_inputs(self, total_amount, address=None):
        '''finds apropriate utxo's to include in rawtx, while being careful
        to never spend old transactions with a lot of coin age.
        Argument is intiger, returns list of apropriate UTXO's'''

        utxos = []
        utxo_sum = Decimal(-0.01)  # starts from negative due to minimal fee
        for tx in sorted(self.listunspent(address=address), key=itemgetter('confirmations')):

            if tx["address"] not in (self.pa_parameters.P2TH_addr,
                                     self.pa_parameters.test_P2TH_addr):

                utxos.append(
                        MutableTxIn(txid=tx['txid'],
                                    txout=tx['vout'],
                                    sequence=Sequence.max(),
                                    script_sig=ScriptSig.empty())
                         )

                utxo_sum += Decimal(tx["amount"])
                if utxo_sum >= total_amount:
                    return {'utxos': utxos, 'total': utxo_sum}

        if utxo_sum < total_amount:
            raise InsufficientFunds("Insufficient funds.")

    @property
    def is_testnet(self):
        '''check if node is configured to use testnet or mainnet'''

        if self.getinfo()["testnet"] is True:
            return True
        else:
            return False

    @property
    def network(self):
        '''return which network is the node operating on.'''

        if self.is_testnet:
            return "tppc"
        else:
            return "ppc"

    def listunspent(self, minconf=1, maxconf=999999, address=None):
        '''list UTXOs
        modified version to allow filtering by address.
        '''
        if address:
            return [u for u in self.req("listunspent", [minconf, maxconf]) if u["address"] == address]
        else:
            return self.req("listunspent", [minconf, maxconf])

