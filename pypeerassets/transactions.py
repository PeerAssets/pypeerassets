'''transaction assembly/dissasembly'''

from decimal import Decimal, getcontext
from math import ceil
from time import time

from btcpy.structs.address import Address
from btcpy.structs.script import (
    NulldataScript,
    P2pkhScript,
    ScriptSig,
    StackData,
)
from btcpy.structs.transaction import (
    Locktime,
    Transaction,
    TxIn,
    TxOut,
)

from pypeerassets.kutil import Kutil
from pypeerassets.provider import Provider


getcontext().prec = 6


def calculate_tx_fee(tx_size: int) -> Decimal:
    '''return tx fee from tx size in bytes'''

    min_fee = Decimal(0.01)  # minimum

    return Decimal(ceil(tx_size / 1000) * min_fee)


def nulldata_script(data: bytes) -> NulldataScript:
    '''create nulldata (OP_return) script'''

    stack = StackData.from_bytes(data)
    return NulldataScript(stack)


def p2pkh_script(address: str) -> P2pkhScript:
    '''create pay-to-key-hash (P2PKH) script'''

    addr = Address.from_string(address)

    return P2pkhScript(addr)


def tx_output(value: Decimal, n: int, script: ScriptSig) -> TxOut:
    '''create TxOut object'''

    return TxOut(value=int(value * 1000000), n=n, script_pubkey=script)


def make_raw_transaction(
    inputs: list,
    outputs: list,
    locktime: Locktime=Locktime(0),
    timestamp: int=int(time()),
    version: int=1,
) -> Transaction:
    '''create raw transaction'''

    return Transaction(version=version, timestamp=timestamp,
                       ins=inputs, outs=outputs,
                       locktime=locktime)


def find_parent_outputs(provider: Provider, utxo: TxIn) -> TxOut:
    '''due to design of the btcpy library, TxIn object must be converted to TxOut object before signing'''

    index = utxo.txout  # utxo index
    return TxOut.from_json(provider.getrawtransaction(utxo.txid, 1)['vout'][index])


def sign_transaction(provider: Provider, unsigned_tx: Transaction,
                     key: Kutil) -> Transaction:
    '''sign transaction with Kutil'''

    parent_output = find_parent_outputs(provider, unsigned_tx.ins[0])
    return key.sign_transaction(parent_output, unsigned_tx)


def _increase_fee_and_sign(provider: Provider, key: Kutil, change_sum: Decimal,
                           inputs: dict, txouts: list) -> Transaction:
    '''when minimal fee wont cut it'''

    # change output is last of transaction outputs
    txouts[-1] = tx_output(value=change_sum, n=txouts[-1].n, script=txouts[-1].script_pubkey)

    unsigned_tx = make_raw_transaction(inputs['utxos'], txouts)
    signed = sign_transaction(provider, unsigned_tx, key)

    return signed
