import pytest
import time
from decimal import Decimal


from btcpy.structs.address import (
    Address,
    InvalidAddress,
    P2pkhAddress,
    P2shAddress,
)
from btcpy.structs.script import P2pkhScript
from btcpy.structs.transaction import (
    Locktime,
    TxOut,
)

from pypeerassets.networks import PeercoinTestnet, PeercoinMainnet, net_query
from pypeerassets.transactions import (
    MutableTransaction,
    Transaction,
    calculate_tx_fee,
    make_raw_transaction,
    p2pkh_script,
    tx_output,
    sign_transaction
)

import pypeerassets as pa


def test_peercoin_address_success():
    good_addresses = {
        ('PeercoinMainnet', P2pkhAddress, 'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw',),
        ('PeercoinTestnet', P2pkhAddress, 'mj46gUeZgeD9ufU7Fvz2dWqaX6Nswtbpba',),
        ('PeercoinTestnet', P2pkhAddress, 'n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj',),
        ('PeercoinMainnet', P2shAddress, 'p92W3t7YkKfQEPDb7cG9jQ6iMh7cpKLvwK',),
    }
    for net, addr_type, address in good_addresses:
        net = PeercoinMainnet if net == 'PeercoinMainnet' else PeercoinTestnet
        from_string = Address.from_string(address, network=net)
        assert address == str(from_string)
        assert from_string.__class__ == addr_type
        assert from_string.network == net


def test_peercoin_address_failure():
    bad_addresses = {
        'vioqwV3F4YzpgnfyUukGVMB3Hv83ujehKCiGWyrYyx2Z7hiKQy7SWUV9KgfMdV9J',
        'bc1a',
        '3rE3tz',
        '1KKKK6N21XKo48zWKuQKXdvSsCf95ibHFa',
    }
    for address in bad_addresses:
        with pytest.raises(InvalidAddress):
            Address.from_string(address, network=PeercoinMainnet)


def test_peercoin_tx_unhexilify():
    """Check that we can parse a Peercoin Transaction from hex encoded bytes.
    Data from:

    In [1]: import pypeerassets as pa

    In [2]: provider = Explorer(network='tppc')

    In [3]: raw = provider.getrawtransaction('c418f3bded92ebc035cfefc93f54dc8a501702e6ad4e6a26a07aab87f4cfb653')
    """
    raw = '01000000f7ae3b5b01b3a00d828f5a9a8e908fb59353b4a87132a75a6d939c6e9338e3727631a65028010000006c493046022100e3a72a3a9f53eab66186da5354a58a6fb4b4fc96c5836445bce0b3755840653f022100f7013eb0c3bbd901a8e9c4935edefa9765fa5dd2f1f3a276634d248a4e17c59801210207c75090d56b94a9f638b8b9abaa346c053db265f4aa752170b86c32cdec7efbffffffff0260d3e815000000001976a914c8ec65800888c2c4f831826ba7e10603b3692db188ac00e1f505000000001976a914ba96e0c304ad07afb115d7019b9e54db96668f9988ac00000000'
    Transaction.unhexlify(raw, network=PeercoinTestnet)


@pytest.mark.parametrize("tx_size", [181, 311])
def test_calculate_transaction_fee(tx_size):

    assert round(calculate_tx_fee(tx_size), 2) == round(Decimal(0.01), 2)


@pytest.mark.parametrize("network", ['peercoin'])
def test_tx_output(network):

    if network == 'peercoin':
        addr = 'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw'

    script = p2pkh_script(network, addr)

    txout = tx_output(network=network, value=Decimal(1.35),
                      n=1, script=script
                      )

    assert isinstance(txout, TxOut)


def test_nulldata_script():

    null = tx_output(network='peercoin-testnet',
                     value=Decimal(0), n=1,
                     script='Oh Hello.'.encode('utf-8'))

    assert isinstance(null, TxOut)


def test_p2pkh_script():

    addr = 'mvWDumZZZVD2nEC7hmsX8dMSHoGHAq5b6d'
    script = p2pkh_script('tppc', addr)

    assert isinstance(script, P2pkhScript)


def test_make_raw_transaction():

    tx = make_raw_transaction("peercoin", [], [], Locktime(300000))
    assert isinstance(tx, MutableTransaction)


def test_sign_transaction():

    network_params = net_query('tppc')

    provider = Cryptoid(network='tppc')
    key = pa.Kutil(network='tppc',
                   privkey=bytearray.fromhex('9e321f5379c2d1c4327c12227e1226a7c2e08342d88431dcbb0063e1e715a36c')
                   )
    dest_address = pa.Kutil(network='tppc').address
    unspent = provider.select_inputs(key.address, 1)

    output = tx_output(network='tppc',
                       value=Decimal(0.1),
                       n=0, script=p2pkh_script(network='tppc',
                                                address=dest_address)
                       )

    unsigned = MutableTransaction(
        version=1,
        ins=unspent['utxos'],
        outs=[output],
        locktime=Locktime(0),
        network=network_params,
        timestamp=int(time.time()),
    )

    assert isinstance(sign_transaction(provider, unsigned, key), Transaction)
