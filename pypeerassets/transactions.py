
'''transaction assembly/dissasembly'''

from pypeerassets.base58 import b58decode
from binascii import hexlify, unhexlify
from .networks import query, networks
from time import time
import struct

OP_RETURN = b'\x6a'
OP_PUSHDATA1 = b'\x4c'
OP_DUP = b'\x76'
OP_HASH160 = b'\xa9'
OP_EQUALVERIFY = b'\x88'
OP_CHECKSIG = b'\xac'
OP_1 = b'\x51'
OP_2 = b'\x52'
OP_3 = b'\x53'
OP_CHECKMULTISIG = b'\xae'
OP_EQUAL = b'\x87'

class Tx_buffer:
    '''helper class for unpacking binary data'''

    def __init__(self, data, ptr=0):
        self.data = data
        self.len = len(data)
        self.ptr = ptr

    def shift(self, chars):
        prefix = self.data[self.ptr:self.ptr+chars]
        self.ptr += chars

        return prefix

    def shift_unpack(self, chars, format):
        unpack = struct.unpack(format, self.shift(chars))

        return unpack[0]

    def shift_varint(self):
        value = self.shift_unpack(1, 'B')

        if value == 0xFF:
            value = self.shift_uint64()
        elif value == 0xFE:
            value = self.shift_unpack(4, '<L')
        elif value == 0xFD:
            value = self.shift_unpack(2, '<H')

        return value

    def shift_uint64(self):
        return self.shift_unpack(4, '<L') + 4294967296 * self.shift_unpack(4, '<L')

    def used(self):
        return min(self.ptr, self.len)

    def remaining(self):
        return max(self.len - self.ptr, 0)


def get_hash160(address):
    '''return ripemd160 hash of the pubkey form the address'''

    return b58decode(address)[1:-4]

def op_push(n: int) -> bytes:

    if n < 0x4c:
        return (n).to_bytes(1, byteorder='little')              # Push n bytes.
    elif n <= 0xff:
        return b'\x4c' + (n).to_bytes(1, byteorder='little')    # OP_PUSHDATA1
    elif n <= 0xffff:
        return b'\x4d' + (n).to_bytes(2, byteorder='little')    # OP_PUSHDATA2
    else:
        return b'\x4e' + (n).to_bytes(4, byteorder='little')    # OP_PUSHDATA4

def var_int(i: int) -> bytes:

    if i < 0xfd:
        return (i).to_bytes(1, byteorder='little')
    elif i <= 0xffff:
        return b'\xfd' + (i).to_bytes(2, byteorder='little')
    elif i <= 0xffffffff:
        return b'\xfe' + (i).to_bytes(4, byteorder='little')
    else:
        return b'\xff' + (i).to_bytes(8, byteorder='little')

def pack_uint64(i: int) -> bytes:
    upper = int(i / 4294967296)
    lower = i - upper * 4294967296

    return struct.pack('<L', lower) + struct.pack('<L', upper)

def monosig_script(address: str) -> bytes:
    '''returns a mono-signature output script'''

    hash160 = get_hash160(address)
    n = len(hash160)
    script = OP_DUP + OP_HASH160 + op_push(n) + hash160 + OP_EQUALVERIFY + OP_CHECKSIG
    return script

def op_return_script(data: bytes) -> bytes:
    '''returns a single OP_RETURN output script'''

    data = hexlify(data)
    script = hexlify(OP_RETURN + op_push(len(data)//2)) + data
    return unhexlify(script)

def make_raw_transaction(network: str, inputs: list, outputs: list,
                         sequence_number=b'\xff\xff\xff\xff', lock_time=b'\x00\x00\x00\x00') -> bytes:
    ''' inputs expected as [{'txid':txhash,'vout':index,'scriptSig':txinScript},..]
        ouputs expected as [{'redeem':peertoshis,'outputScript': outputScript},...]
    '''

    raw_tx = b'\x01\x00\x00\x00' # 4 byte version number
    network_vars = query(network)

    if network_vars.tx_timestamp:
        raw_tx += struct.pack('<L', int(time())) # 4 byte timestamp (Peercoin specific)

    raw_tx += var_int(len(inputs)) # varint for number of inputs

    for utxo in inputs:
        raw_tx += utxo['txid'][::-1] # previous transaction hash (reversed)
        raw_tx += struct.pack('<L', utxo['vout']) # previous txout index
        raw_tx += var_int(len(utxo['scriptSig'])) # scriptSig length
        raw_tx += utxo['scriptSig'] # scriptSig
        raw_tx += sequence_number # sequence number (irrelevant unless nLockTime > 0)

    raw_tx += var_int(len(outputs)) # varint for number of outputs

    for output in outputs:
        raw_tx += pack_uint64(int(round(output['redeem'] * network_vars.denomination ))) # value in peertoshi's or satoshi's
        raw_tx += var_int(len(output['outputScript']))
        raw_tx += output['outputScript']

    raw_tx += lock_time # nLockTime

    return raw_tx

def unpack_txn_buffer(buffer: Tx_buffer, network: str) -> dict:

    txn = {
        'vin': [],
        'vout': [],
        }

    txn['version'] = buffer.shift_unpack(4, '<L') # small-endian 32-bits
    if query(network).tx_timestamp: # peercoin: add 4 byte timestamp
        txn['timestamp'] = buffer.shift_unpack(4, '<L') # small-endian 32-bits

    inputs = buffer.shift_varint()
    if inputs > 100000: # sanity check
        return None

    for _ in range(inputs):
        _input = {}

        _input['txid'] = hexlify(buffer.shift(32)[::-1]).decode()
        _input['vout'] = buffer.shift_unpack(4, '<L')
        length = buffer.shift_varint()
        _input['scriptSig'] = hexlify(buffer.shift(length)).decode()
        _input['sequence'] = buffer.shift_unpack(4, '<L')

        txn['vin'].append(_input)

    outputs = buffer.shift_varint()
    if outputs > 100000: # sanity check
        return None

    for _ in range(outputs):
        output = {}

        output['value'] = float(buffer.shift_uint64()) / query(network).denomination
        length = buffer.shift_varint()
        output['scriptPubKey'] = hexlify(buffer.shift(length)).decode()

        txn['vout'].append(output)

    txn['locktime'] = buffer.shift_unpack(4, '<L')

    return txn

def unpack_raw_transaction(rawtx: bytes) -> dict:
    '''unpacks raw transactions, returns dictionary'''

    return unpack_txn_buffer(Tx_buffer(rawtx))
