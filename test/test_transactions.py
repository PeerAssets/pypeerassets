import pytest
from binascii import unhexlify, hexlify
from pypeerassets.transactions import *


def test_tx_buffer():
    '''test tx_buffer transaction unpacking class'''

    rawtx = '''01000000c2376d59010000000000000000000000000000000000000000000000000000000000000000ffffffff0e033b5d04026102062f503253482fffffffff0100000000000000000000000000'''

    t = Tx_buffer(unhexlify(rawtx))

    d = {
        'data': b'\x01\x00\x00\x00\xc27mY\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x0e\x03;]\x04\x02a\x02\x06/P2SH/\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        'len': 78,
        'ptr': 0}

    assert t.__dict__ == d


def test_get_hash_160():

    address = "PUsvrXxav7ryMawmxZk9ShmGiuCJWjdPmo"
    assert get_hash160(address) == b'\xde\x8d\xa6A3P\x18\x8b\x95H\x8d\xb2\xf9\tmu\xb6U\xfc\xc7'


@pytest.mark.parametrize("num", [0, 1, 5, 111])
def test_op_push(num):

    if num == 0:
        assert op_push(num) == b'\x00'

    if num == 1:
        assert op_push(num) == b'\x01'

    if num == 5:
        assert op_push(num) == b'\x05'

    if num == 111:
        assert op_push(num) == b'Lo'


@pytest.mark.parametrize("num", [0, 1, 5, 111])
def test_var_int(num):

    if num == 0:
        assert var_int(num) == b'\x00'

    if num == 1:
        assert var_int(num) == b'\x01'

    if num == 5:
        assert var_int(num) == b'\x05'

    if num == 111:
        assert var_int(num) == b'o'


@pytest.mark.parametrize("num", [0, 10, 32])
def test_pack_uint64(num):

    if num == 0:
        assert pack_uint64(num) == b'\x00\x00\x00\x00\x00\x00\x00\x00'

    if num == 10:
        assert pack_uint64(num) == b'\n\x00\x00\x00\x00\x00\x00\x00'

    if num == 32:
        assert pack_uint64(num) == b' \x00\x00\x00\x00\x00\x00\x00'


def test_monosig_script():

    assert monosig_script("n2uLuStAtNYeJyzJCCJpTAueVAoAjX8erb") == b'v\xa9\x14\xea\x96\xaa\xab\xcb\xeb\x82f\xbe\xbb\xddd\xd1\xbcy(\xbe\x1b\xc0J\x88\xac'


def test_op_return_script():

    assert op_return_script("kokolomoj".encode()) == b'j\tkokolomoj'


def test_transaction_dissasembly():
    '''verifies that transaction dissasembly is in order'''

    tx = "10060b0349d3c84a7d88bd396a703d6df39c587bf8169fef73db46e7b346efe5"
    rawtx = "0100000055842d5801893e129cc07ed2799eef39c3961baec2ce58e273ce51ae9f16fd92be9924bbf5020000004a493046022100b4de95eb9652b86fe3070ab9c1ccf60ec700638848589416f48bfaa0342c2d46022100ed7ff3ec83324c146e3ce8123854a62a9953f6ebd027b77330a1c2b9f0a5847501ffffffff020000000000000000007096050d000000002321027f2101a1eb0ef4f53ab48919a0f390dfcaddd6b8104324b4ef8d2654b08b3722ac00000000"

    # decoded by ppcoind
    decoded_raw_tx = {
        'vout': [
            {'scriptPubKey': '', 'value': 0.0},
            {'scriptPubKey': '21027f2101a1eb0ef4f53ab48919a0f390dfcaddd6b8104324b4ef8d2654b08b3722ac',
                'value': 218.47}
        ],
        'timestamp': 1479378005,
        'version': 1,
        'vin': [
            {
                'vout': 2,
                'sequence': 4294967295,
                'scriptSig': '493046022100b4de95eb9652b86fe3070ab9c1ccf60ec700638848589416f48bfaa0342c2d46022100ed7ff3ec83324c146e3ce8123854a62a9953f6ebd027b77330a1c2b9f0a5847501',
                'txid': 'f5bb2499be92fd169fae51ce73e258cec2ae1b96c339ef9e79d27ec09c123e89'
            }
        ],
        'locktime': 0
    }

    assert unpack_raw_transaction(rawtx=rawtx, network="ppc") == decoded_raw_tx


def test_transaction_assembly():
    '''verifies that transaction assembly is functioning properly'''

    prev_txid = unhexlify('4fe5233fe5b25047730e41fc2fcdbaf270aa01a35c6292f13ab7432529d6d293')

    inputs = [{'txid': prev_txid,
                'vout':2,
                'scriptSig': unhexlify('483045022057a5995013c8c55a16c1f692d91881fef443a467316d73a15abd65b6ca6c77dd022100f349283acebe70c2be16dcfd7860aa530e920e74f7a4afeb905d58d73e381ce2012103cd1236a7327457047f596e621b7dfa4a923cfdafffd6094e12db09f0f5695b4d')}]

    outputs = [{'redeem': 123,
                'outputScript': unhexlify('76a9141e667ee94ea8e62c63fe59a0269bb3c091c86ca388ac')}]

    raw_tx = make_raw_transaction(inputs=inputs, outputs=outputs, network='ppc')

    # split on vin[0] txid to make test time independent
    split = raw_tx.split(prev_txid[::-1]) # txid is stored reversed

    assert len(split) > 1, 'Failed to find vin[0] txid in raw_tx'

    # Match the remainder
    assert hexlify(split[1]) == b'020000006b483045022057a5995013c8c55a16c1f692d91881fef443a467316d73a15abd65b6ca6c77dd022100f349283acebe70c2be16dcfd7860aa530e920e74f7a4afeb905d58d73e381ce2012103cd1236a7327457047f596e621b7dfa4a923cfdafffd6094e12db09f0f5695b4dffffffff01c0d45407000000001976a9141e667ee94ea8e62c63fe59a0269bb3c091c86ca388ac00000000'
    
def test_asm_from_hex():
    from binascii import unhexlify
    global scripts
    '''check if asm generated is what is expected from hex script.'''
    
    scripts = {
        "2103995e7a655184e166ef48d0e15e126deaff6f3c07e415ef6f9e45645543579536ac":
        "03995e7a655184e166ef48d0e15e126deaff6f3c07e415ef6f9e45645543579536 OP_CHECKSIG",
        "2102aa1af77d813d9ab98fe7447c3a735323709bd42cacaa1777b3d0dd35e98bbc61ac":
        "02aa1af77d813d9ab98fe7447c3a735323709bd42cacaa1777b3d0dd35e98bbc61 OP_CHECKSIG",
        "76a9140f39a0043cf7bdbe429c17e8b514599e9ec53dea88ac":
        "OP_DUP OP_HASH160 0f39a0043cf7bdbe429c17e8b514599e9ec53dea OP_EQUALVERIFY OP_CHECKSIG",
        "76a9146759a0764127ae9047bff989f330bc2c5d0cfa1e88ac":
        "OP_DUP OP_HASH160 6759a0764127ae9047bff989f330bc2c5d0cfa1e OP_EQUALVERIFY OP_CHECKSIG",
        "6a140801120e4d79206c6974746c6520706f6e792004":
        "OP_RETURN 0801120e4d79206c6974746c6520706f6e792004",
    }

    for key, value in scripts.items():
        assert script_asm(unhexlify(key))["asm"] == value
