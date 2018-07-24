'''transaction assembly/dissasembly'''

from decimal import Decimal
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
    MutableTransaction,
    Transaction,
    TxIn,
    TxOut,
)

from pypeerassets.btcpy_peercoin import PeercoinMutableTx
from pypeerassets.kutil import Kutil
from pypeerassets.networks import net_query
from pypeerassets.provider import Provider


def calculate_tx_fee(tx_size: int) -> Decimal:
    '''return tx fee from tx size in bytes'''

    min_fee = Decimal(0.01)  # minimum

    return Decimal(ceil(tx_size / 1000) * min_fee)


def nulldata_script(data: bytes) -> NulldataScript:
    '''create nulldata (OP_return) script'''

    stack = StackData.from_bytes(data)
    return NulldataScript(stack)


def p2pkh_script(network: str, address: str) -> P2pkhScript:
    '''create pay-to-key-hash (P2PKH) script'''

    network_params = net_query(network)

    addr = Address.from_string(network=network_params,
                               string=address)

    return P2pkhScript(addr)


def tx_output(network: str, value: Decimal, n: int,
              script: ScriptSig) -> TxOut:
    '''create TxOut object'''

    network_params = net_query(network)

    return TxOut(network=network_params,
                 value=int(value * network_params.to_unit),
                 n=n, script_pubkey=script)


def make_raw_transaction(
    network: str,
    inputs: list,
    outputs: list,
    locktime: Locktime,
    timestamp: int=int(time()),
    version: int=1,
) -> MutableTransaction:
    '''create raw transaction'''

    network_params = net_query(network)

    if network_params.name.startswith("peercoin"):
        return PeercoinMutableTx(
            version=version,
            timestamp=timestamp,
            ins=inputs,
            outs=outputs,
            locktime=locktime,
            network=network_params,
        )

    return MutableTransaction(
        version=version,
        ins=inputs,
        outs=outputs,
        locktime=locktime,
        network=network_params,
    )


def find_parent_outputs(provider: Provider, utxo: TxIn) -> TxOut:
    '''due to design of the btcpy library, TxIn object must be converted to TxOut object before signing'''

    network_params = net_query(provider.network)
    index = utxo.txout  # utxo index
    return TxOut.from_json(provider.getrawtransaction(utxo.txid,
                           1)['vout'][index],
                           network=network_params)


def sign_transaction(provider: Provider, unsigned: MutableTransaction,
                     key: Kutil) -> Transaction:
    '''sign transaction with Kutil'''

    parent_outputs = [find_parent_outputs(provider, i) for i in unsigned.ins]
    return key.sign_transaction(parent_outputs, unsigned)
