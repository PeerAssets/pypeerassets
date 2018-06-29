

import pytest
from decimal import Decimal

from btcpy.structs.transaction import (
    Locktime,
    TxOut,
    PeercoinTx,
    Transaction
)

from pypeerassets.transactions import (
    calculate_tx_fee,
    make_raw_transaction,
    p2pkh_script,
    tx_output
)


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

    txout = tx_output(network=network, value=Decimal(0),
                      n=1, script=script
                      )

    assert isinstance(txout, TxOut)


def test_nulldata_script():
    pass


def test_p2pkh_script():
    pass


def test_make_raw_transaction():
    tx = make_raw_transaction("bitcoin", [], [], Locktime(0))
    assert isinstance(tx, Transaction)

    tx = make_raw_transaction("peercoin", [], [], Locktime(0))
    assert isinstance(tx, PeercoinTx)
