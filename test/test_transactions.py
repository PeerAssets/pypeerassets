import pytest
from decimal import Decimal, getcontext
getcontext().prec = 6
from pypeerassets.transactions import *


@pytest.mark.parametrize("tx_size", [181, 311])
def test_calculate_transaction_fee(tx_size):

    assert round(calculate_tx_fee(tx_size), 2) == round(Decimal(0.01), 2)


def test_nulldata_script():
    pass


def test_p2pkh_script():
    pass

