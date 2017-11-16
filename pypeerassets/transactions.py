
'''transaction assembly/dissasembly'''

from time import time
from math import ceil
from decimal import Decimal, getcontext
getcontext().prec = 6
from btcpy.structs.address import Address
from btcpy.structs.transaction import TxOut, TxIn, Sequence, Locktime, MutableTransaction
from btcpy.structs.script import StackData, ScriptSig, NulldataScript, ScriptSig, ScriptPubKey
from btcpy.structs.script import P2pkhScript, MultisigScript, P2shScript
from .networks import query


def calculate_tx_fee(tx_size: int) -> Decimal:
    '''return tx fee from tx size in bytes'''

    min_fee = Decimal(0.01)  # minimum

    return Decimal(ceil(tx_size / 1000) * min_fee)


def nulldata_script(data: bytes):
    '''create nulldata (OP_return) script'''

    stack = StackData.from_bytes(data)
    return NulldataScript(stack)


def p2pkh_script(address: str):
    '''create pay-to-key-hash (P2PKH) script'''

    addr = Address.from_string(address)

    return P2pkhScript(addr)


def tx_output(value: Decimal, n: int, script: ScriptSig) -> TxOut:
    '''create TxOut object'''

    return TxOut(value=int(value * 1000000), n=n, script_pubkey=script)


def make_raw_transaction(inputs: list, outputs: list, locktime=Locktime(0),
                         timestamp: int=int(time()), version=1):
    '''create raw transaction'''

    return MutableTransaction(version, timestamp, inputs, outputs, locktime)


def find_parent_outputs(provider, utxo: TxIn):
    '''due to design of the btcpy library, TxIn object must be converted to TxOut object before signing'''

    index = utxo.txout  # utxo index
    return TxOut.from_json(provider.getrawtransaction(utxo.txid)['vout'][index])
