
'''transaction assembly/dissasembly'''

from time import time
from btcpy.structs.address import Address
from btcpy.structs.transaction import TxOut, TxIn, Sequence, Locktime, MutableTransaction
from btcpy.structs.script import StackData, ScriptSig, NulldataScript, ScriptSig, ScriptPubKey
from btcpy.structs.script import P2pkhScript, MultisigScript, P2shScript
from .networks import query


def nulldata_output(data: bytes, seq: int, value=0):
    '''create nulldata (OP_return) output'''

    stack = StackData.from_bytes(data)
    op_ret = NulldataScript(stack)
    return TxOut(value, seq, op_ret)


def monosig_p2pkh(address: str):
    '''create pay-to-key-hash (P2PKH) script'''

    addr = Address.from_string(address)

    return P2pkhScript(addr)


def tx_output(value: float, seq: int, script: ScriptSig):
    '''create TxOut object'''

    return TxOut(int(value * 1000000), seq, script)


def make_raw_transaction(inputs: list, outputs: list, locktime=Locktime(0),
                         timestamp: int=int(time()), version=1):
    '''create raw transaction'''

    return MutableTransaction(version, timestamp, inputs, outputs, locktime)
