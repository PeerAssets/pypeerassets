

import pytest
import time
from decimal import Decimal

from btcpy.structs.transaction import (
    Locktime,
    TxOut,
    MutableTransaction,
    PeercoinMutableTx,
    Transaction
)

from btcpy.structs.script import P2pkhScript

from pypeerassets.transactions import (
    calculate_tx_fee,
    make_raw_transaction,
    p2pkh_script,
    tx_output,
    sign_transaction
)

from pypeerassets.networks import net_query
import pypeerassets as pa


@pytest.mark.parametrize("tx_size", [181, 311])
def test_calculate_transaction_fee(tx_size):

    assert round(calculate_tx_fee(tx_size), 2) == round(Decimal(0.01), 2)


@pytest.mark.parametrize("network", ['bitcoin', 'peercoin'])
def test_tx_output(network):

    if network == 'peercoin':
        addr = 'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw'
    if network == 'bitcoin':
        addr = '1FV9w4NvBnnNp4GMUNuqfzqGKvgBY5YTSB'

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

    addr = '1FV9w4NvBnnNp4GMUNuqfzqGKvgBY5YTSB'
    script = p2pkh_script('bitcoin', addr)

    assert isinstance(script, P2pkhScript)


def test_make_raw_transaction():

    tx = make_raw_transaction("bitcoin", [], [], Locktime(0))
    assert isinstance(tx, MutableTransaction)

    tx = make_raw_transaction("peercoin", [], [], Locktime(300000))
    assert isinstance(tx, MutableTransaction)


def test_sign_transaction():

    network_params = net_query('tppc')

    provider = pa.Cryptoid(network='tppc')
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

    unsigned = PeercoinMutableTx(version=1,
                                 timestamp=int(time.time()),
                                 ins=unspent['utxos'],
                                 outs=[output],
                                 locktime=Locktime(0),
                                 network=network_params.btcpy_constants
                                 )

    assert isinstance(sign_transaction(provider, unsigned, key), Transaction)
