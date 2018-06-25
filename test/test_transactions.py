from decimal import Decimal, getcontext

from btcpy.structs.transaction import (
    Locktime,
    PeercoinTx,
    Transaction,
)
import pytest

from pypeerassets.transactions import (
    calculate_tx_fee,
    make_raw_transaction,
)


getcontext().prec = 6


@pytest.mark.parametrize("tx_size", [181, 311])
def test_calculate_transaction_fee(tx_size):

    assert round(calculate_tx_fee(tx_size), 2) == round(Decimal(0.01), 2)


def test_nulldata_script():
    pass


def test_p2pkh_script():
    pass


def test_make_raw_transaction():
    tx = make_raw_transaction("bitcoin", [], [], Locktime(0))
    assert isinstance(tx, Transaction)

    tx = make_raw_transaction("peercoin", [], [], Locktime(0))
    assert isinstance(tx, PeercoinTx)
