
'''transaction assembly/dissasembly'''

from base58 import b58decode
from binascii import hexlify, unhexlify
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

def get_hash160(address):
    '''return ripemd160 hash of the pubkey form the address'''

    return b58decode(address)[1:-4]

def op_push(n):

    if n < 0x4c:
        return (n).to_bytes(1, byteorder='little')              # Push n bytes.
    elif n <= 0xff:
        return b'\x4c' + (n).to_bytes(1, byteorder='little')    # OP_PUSHDATA1
    elif n <= 0xffff:
        return b'\x4d' + (n).to_bytes(2, byteorder='little')    # OP_PUSHDATA2
    else:
        return b'\x4e' + (n).to_bytes(4, byteorder='little')    # OP_PUSHDATA4

def var_int(i):

    if i < 0xfd:
        return hexlify((i).to_bytes(1, byteorder='little'))
    elif i <= 0xffff:
        return hexlify(b'\xfd' + (i).to_bytes(2, byteorder='little'))
    elif i <= 0xffffffff:
        return hexlify(b'\xfe' + (i).to_bytes(4, byteorder='little'))
    else:
        return hexlify(b'\xff' + (i).to_bytes(8, byteorder='little'))
    
def pack_uint64(i):
    upper = int(i / 4294967296)
    lower = i - upper * 4294967296

    return hexlify(struct.pack('<L', lower) + struct.pack('<L', upper))

def monosig_script(address):
    '''returns a mono-signature output script'''

    hash160 = get_hash160(address)
    n = len(hash160)
    script = hexlify(OP_DUP + OP_HASH160 + op_push(n) + hash160 + OP_EQUALVERIFY + OP_CHECKSIG)
    return script

def op_return_script(data):
    '''returns a single OP_RETURN output script'''

    data = hexlify(data.encode('utf-8'))
    script = hexlify(OP_RETURN + op_push(len(data))) + data
    return script

def make_raw_transaction(inputs, outputs, network='ppc'):
    ''' inputs expected as [{'txid':txhash,'vout':index,'scriptSig':txinScript},..]
        ouputs expected as [{'redeem':peertoshis,'outputScript': outputScript},...]
    '''
    raw_tx = b'01000000' # 4 byte version number

    if network is "ppc" or network is "tppc":
        raw_tx += hexlify(struct.pack('<L', int(time()))) # 4 byte timestamp (Peercoin specific)

    raw_tx += var_int(len(inputs)) # varint for number of inputs

    for utxo in inputs:
        raw_tx += utxo['txid'][::-1].encode("utf-8") # previous transaction hash (reversed)
        raw_tx += hexlify(struct.pack('<L', utxo['vout'])) # previous txout index
        raw_tx += var_int(len(utxo['scriptSig'])//2) # scriptSig length
        raw_tx += utxo['scriptSig'].encode("utf-8") # scriptSig
        raw_tx += b'ffffffff' # sequence number (irrelevant unless nLockTime > 0)

    raw_tx += var_int(len(outputs)) # varint for number of outputs

    for output in outputs:
        raw_tx += pack_uint64(int(round(output['redeem'] * 1000000 ))) # value in peertoshi'
        raw_tx += var_int(len(output['outputScript'])//2)
        raw_tx += output['outputScript']

    raw_tx += b'00000000' # nLockTime

    return raw_tx

    
