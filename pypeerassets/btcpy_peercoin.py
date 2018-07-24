"Overrides that make btcpy work with Peercoin :)"

from binascii import unhexlify
from decimal import Decimal

from btcpy.lib.parsing import Parser, TransactionParser
from btcpy.lib.types import Mutable, cached
from btcpy.structs.script import CoinBaseScriptSig, ScriptBuilder
from btcpy.structs.transaction import (
    Locktime,
    MutableTransaction,
    MutableTxIn,
    Stream,
    Transaction,
    TxIn,
    TxOut,
)

from pypeerassets.networks import PeercoinMainnet


class PeercoinTx(Transaction):

    def __init__(self, version: int, timestamp: int, ins: list, outs: list,
                 locktime: Locktime, txid: str=None, network=PeercoinMainnet) -> None:

        object.__setattr__(self, 'version', version)
        object.__setattr__(self, 'timestamp', timestamp)
        object.__setattr__(self, 'ins', tuple(ins))
        object.__setattr__(self, 'outs', tuple(outs))
        object.__setattr__(self, 'locktime', locktime)
        object.__setattr__(self, '_txid', txid)
        object.__setattr__(self, 'network', network)

        if txid != self.txid and txid is not None:
            raise ValueError('txid {} does not match transaction data {}'.format(txid, self.hexlify()))

    @classmethod
    def unhexlify(cls, string, network=PeercoinMainnet):
        return cls.deserialize(bytearray(unhexlify(string)), network=network)

    @classmethod
    def deserialize(cls, string, network=PeercoinMainnet):
        parser = PeercoinTxParser(string, network=network)
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
            timestamp=tx_json['time'],
            locktime=Locktime(tx_json['locktime']),
            txid=tx_json['txid'],
            ins=[TxIn.from_json(txin_json) for txin_json in tx_json['vin']],
            outs=[TxOut.from_json(txout_json) for txout_json in tx_json['vout']],
            network=network,
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
        return PeercoinMutableTx(
            version=self.version,
            timestamp=self.timestamp,
            ins=[txin.to_mutable() for txin in self.ins],
            outs=self.outs,
            locktime=self.locktime,
            network=self.network,
        )

    def __str__(self):
        return ('PeercoinTx(version={}, '
                'ins=[{}], '
                'outs=[{}], '
                'locktime={}, '
                'timestamp={} '.format(self.version,
                                       ', '.join(str(txin) for txin in self.ins),
                                       ', '.join(str(out) for out in self.outs),
                                       self.locktime,
                                       self.timestamp))


class PeercoinMutableTx(PeercoinTx, MutableTransaction):

    def __init__(self, version: int, timestamp: int, ins: list,
                 outs: list, locktime: Locktime, network=PeercoinMainnet) -> None:

        super().__init__(version, timestamp, ins, outs, locktime, network=network)
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
        return PeercoinTx(
            self.version,
            self.timestamp,
            [txin.to_immutable() for txin in self.ins],
            self.outs,
            self.locktime,
            network=self.network,
        )

    def to_segwit(self):
        raise NotImplementedError("Peercoin doesn't have SegWit.")


class PeercoinTxOut(TxOut):

    def get_dust_threshold(self, size_to_relay_fee):

        if isinstance(self.script_pubkey, NulldataScript):
            return 0

        return 0.01


class PeercoinTxParser(TransactionParser):

    def _timestamp(self):
        '''get transaction timestamp (peercoin specific)'''
        return int.from_bytes(self >> 4, 'little')

    def _txout(self, n):
        value = int.from_bytes(self >> 8, 'little')
        script = ScriptBuilder.identify(self >> self.parse_varint())
        return PeercoinTxOut(value, n, script, network=self.network)

    def get_next_tx(self, mutable=False):
        version = self._version()
        tstamp = self._timestamp()
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
            result = PeercoinTx(version, tstamp, txins, txouts, locktime, network=self.network)

        return result.to_mutable() if mutable else result
