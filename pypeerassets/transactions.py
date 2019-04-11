'''transaction assembly/dissasembly'''

from decimal import Decimal
from time import time

from btcpy.lib.parsing import Parser, TransactionParser as BtcPyTxParser
from btcpy.lib.types import Mutable, cached
from btcpy.structs.address import Address
from btcpy.structs.script import (
    CoinBaseScriptSig,
    NulldataScript,
    P2pkhScript,
    P2shScript,
    ScriptBuilder,
    ScriptSig,
    StackData,
)
from btcpy.structs.transaction import (
    CoinBaseTxIn,
    Locktime,
    MutableTransaction as BtcPyMutableTx,
    MutableTxIn,
    Stream,
    Transaction as BtcPyTx,
    TxIn,
    TxOut,
    Witness,
)

from pypeerassets.kutil import Kutil
from pypeerassets.networks import PeercoinMainnet, net_query
from pypeerassets.provider import Provider


class Transaction(BtcPyTx):

    def __init__(
        self,
        version: int,
        ins: list,
        outs: list,
        locktime: Locktime,
        txid: str=None,
        network=PeercoinMainnet,
        timestamp: int=0,
    ) -> None:
        object.__setattr__(self, 'version', version)
        object.__setattr__(self, 'ins', tuple(ins))
        object.__setattr__(self, 'outs', tuple(outs))
        object.__setattr__(self, 'locktime', locktime)
        object.__setattr__(self, '_txid', txid)
        object.__setattr__(self, 'network', network)
        object.__setattr__(self, 'timestamp', timestamp)
        if txid != self.txid and txid is not None:
            raise ValueError('txid {} does not match transaction data {}'.format(txid, self.hexlify()))

    @classmethod
    def unhexlify(cls, string, network=PeercoinMainnet):
        return cls.deserialize(bytearray.fromhex(string), network=network)

    @classmethod
    def deserialize(cls, string, network=PeercoinMainnet):
        parser = TransactionParser(string, network=network)
        result = parser.get_next_tx(issubclass(cls, Mutable))
        if parser:
            raise ValueError('Leftover data after transaction')
        if not isinstance(result, cls):
            raise TypeError('Trying to load transaction from wrong transaction serialization')
        return result

    @classmethod
    def from_json(cls, tx_json, network=PeercoinMainnet):
        return cls(
            version=tx_json['version'],
            ins=[TxIn.from_json(txin_json) for txin_json in tx_json['vin']],
            outs=[TxOut.from_json(txout_json) for txout_json in tx_json['vout']],
            locktime=Locktime(tx_json['locktime']),
            txid=tx_json['txid'],
            network=network,
            timestamp=tx_json['time'],
        )

    def to_json(self):
        return {
            'hex': self.hexlify(),
            'txid': self.txid,
            'hash': self.hash(),
            'size': self.size,
            'vsize': self.vsize,
            'version': self.version,
            'timestamp': self.timestamp,
            'locktime': self.locktime.n,
            'vin': [txin.to_json() for txin in self.ins],
            'vout': [txout.to_json() for txout in self.outs],
        }

    @cached
    def serialize(self):
        from itertools import chain
        result = Stream()
        result << self.version.to_bytes(4, 'little')

        if self.network.tx_timestamp:
            result << self.timestamp.to_bytes(4, 'little')

        result << Parser.to_varint(len(self.ins))
        # the most efficient way to flatten a list in python
        result << bytearray(chain.from_iterable(txin.serialize() for txin in self.ins))
        result << Parser.to_varint(len(self.outs))
        # the most efficient way to flatten a list in python
        result << bytearray(chain.from_iterable(txout.serialize() for txout in self.outs))
        result << self.locktime
        return result.serialize()

    def to_mutable(self):
        return MutableTransaction(
            version=self.version,
            ins=[txin.to_mutable() for txin in self.ins],
            outs=self.outs,
            locktime=self.locktime,
            network=self.network,
            timestamp=self.timestamp,
        )

    def __str__(self):
        return ('Transaction(version={}, '
                'ins=[{}], '
                'outs=[{}], '
                'locktime={}, '
                'timestamp={} '.format(self.version,
                                       ', '.join(str(txin) for txin in self.ins),
                                       ', '.join(str(out) for out in self.outs),
                                       self.locktime,
                                       self.timestamp))


class MutableTransaction(Transaction, BtcPyMutableTx):

    def __init__(
        self,
        version: int,
        ins: list,
        outs: list,
        locktime: Locktime,
        network=PeercoinMainnet,
        timestamp: int=0,
    ) -> None:

        super().__init__(version, ins, outs, locktime, network=network, timestamp=timestamp)
        ins = []
        for txin in self.ins:
            if isinstance(txin, MutableTxIn):
                ins.append(txin)
            elif isinstance(txin, TxIn):
                ins.append(txin.to_mutable())
            else:
                raise ValueError('Expected objects of type `TxIn` or `MutableTxIn`, got {} instead'.format(type(txin)))
        self.ins = ins
        self.outs = list(self.outs)

    def to_immutable(self):
        return Transaction(
            self.version,
            [txin.to_immutable() for txin in self.ins],
            self.outs,
            self.locktime,
            network=self.network,
            timestamp=self.timestamp,
        )


class TransactionParser(BtcPyTxParser):

    def _timestamp(self):
        '''get transaction timestamp (peercoin specific)'''
        return int.from_bytes(self >> 4, 'little')

    def _txout(self, n):
        value = int.from_bytes(self >> 8, 'little')
        script = ScriptBuilder.identify(self >> self.parse_varint())
        return self.network.tx_out_cls(value, n, script, network=self.network)

    def get_next_tx(self, mutable=False):
        version = self._version()
        tstamp = self._timestamp() if self.network.tx_timestamp else 0
        segwit, txins_data = self._txins_data()
        txouts = self._txouts()
        if segwit:
            witness = self._witness()
            txins = [CoinBaseTxIn(*txin_data[2:], witness=Witness(wit))
                     if isinstance(txin_data[2], CoinBaseScriptSig)
                     else TxIn(*txin_data, witness=Witness(wit))
                     for txin_data, wit in zip(txins_data, witness)]
        else:
            txins = [CoinBaseTxIn(*txin_data[2:])
                     if isinstance(txin_data[2], CoinBaseScriptSig)
                     else TxIn(*txin_data)
                     for txin_data in txins_data]

        locktime = self._locktime()

        if len(txins) > 1 and isinstance(txins[0], CoinBaseTxIn):
            raise ValueError('Transaction looks like coinbase but has more than one txin')

        if segwit:
            raise Exception('Peercoin does not currently support SegWit.')
        else:
            result = Transaction(version, txins, txouts, locktime, network=self.network, timestamp=tstamp)

        return result.to_mutable() if mutable else result


def calculate_tx_fee(tx_size_bytes: int) -> Decimal:
    '''return tx fee from tx size in bytes'''

    if tx_size_bytes < 1001:
        return Decimal(0.01)

    else:
        return Decimal(round(tx_size_bytes * 0.00001, 5))


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


def p2sh_p2pkh_script(network: str, address: str) -> P2shScript:
    '''p2sh embedding p2pkh'''

    network_params = net_query(network)

    addr = Address.from_string(network=network_params,
                               string=address)

    p2pkh = P2pkhScript(addr)

    return P2shScript(p2pkh)


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
        return MutableTransaction(
            version=version,
            ins=inputs,
            outs=outputs,
            locktime=locktime,
            network=network_params,
            timestamp=timestamp,
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
