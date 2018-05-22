import pytest

from pypeerassets.exceptions import UnsupportedNetwork
from pypeerassets.provider.mintr import Mintr


def test_mintr_only_supports_peercoin_mainnet():
	"""Mintr only supports the peercoin mainnet and will throw an
	UnsupportedNetwork exception if configured for another network.
	"""
	Mintr(network="peercoin")

	with pytest.raises(UnsupportedNetwork):
		Mintr(network="tppc")

	with pytest.raises(UnsupportedNetwork):
		Mintr(network="bitcoin")


def test_mintr_getinfo():

    assert Mintr().getinfo() == {"testnet": False}


def test_mintr_network():

    assert Mintr().network == "peercoin"


def test_mintr_getrawtransaction():

    assert isinstance(Mintr().getrawtransaction("147c4daf47293fb670efd97dd7f9f6e964f515e6478e0cc3a668e4330f12ad6f"), dict)


def test_mintr_getblock():

    assert isinstance(Mintr().getblock('be48bcf5155b4650d75d600bf1e9f37a5a049c2905542c6ced43ec0cb57673e8'), dict)


def test_mintr_listtransaction():

    assert isinstance(Mintr().listtransactions("PPchatrw5hV1y3JUU2kxyL4LQccprbp8FX"), list)
