
'''Communicate with local or remote peercoin-daemon via JSON-RPC'''

from operator import itemgetter
from .common import Provider
from pypeerassets.exceptions import InsufficientFunds
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

    def select_inputs(self, address: str, amount: int) -> dict:
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
                if utxo_sum >= amount:
                    return {'utxos': utxos, 'total': utxo_sum}

        if utxo_sum < amount:
            raise InsufficientFunds("Insufficient funds.")

        raise Exception("undefined behavior :.(")

    @property
    def is_testnet(self) -> bool:
        '''check if node is configured to use testnet or mainnet'''

        if self.getinfo()["testnet"] is True:
            return True
        else:
            return False

    @property
    def network(self) -> str:
        '''return which network is the node operating on.'''

        if self.is_testnet:
            return "tppc"
        else:
            return "ppc"

    def listunspent(
        self,
        address: str="",
        minconf: int=1,
        maxconf: int=999999,
    ) -> list:
        '''list UTXOs
        modified version to allow filtering by address.
        '''
        if address:
            return self.req("listunspent", [minconf, maxconf, [address]])

        return self.req("listunspent", [minconf, maxconf])
