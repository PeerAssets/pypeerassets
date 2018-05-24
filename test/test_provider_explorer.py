import pytest
from decimal import Decimal
from pypeerassets.provider.explorer import Explorer


def test_explorer_is_testnet():

    explorer = Explorer(network="tppc")

    assert isinstance(explorer.is_testnet, bool)
    assert explorer.is_testnet is True


def test_explorer_network():

    assert Explorer(network="ppc").network == "peercoin"


def test_explorer_getblockcount():

    assert isinstance(Explorer(network="ppc").getblockcount(), int)


def test_explorer_getblock():

    provider = Explorer(network="ppc")
    assert isinstance(provider.getblock('00000000000da9a26b4f4ce3f1f286438ec2198e5f60d108fafa700061b486e7'), dict)


def test_explorer_get_block_hash():

    assert isinstance(Explorer(network="ppc").getblockhash(3378), str)


def test_explorer_getdifficulty():

    difficulty = Explorer(network="ppc").getdifficulty()
    assert isinstance(difficulty["proof-of-stake"], float)
    assert isinstance(difficulty["proof-of-work"], float)


def test_explorer_getbalance():

    assert isinstance(Explorer(network="ppc").getbalance(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), Decimal)


def test_explorer_getreceivedbyaddress():

    assert isinstance(Explorer(network="ppc").getreceivedbyaddress(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), Decimal)


def test_explorer_listunspent():

    assert isinstance(Explorer(network="ppc").listunspent(
                      'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw'), list)


@pytest.mark.parametrize("decrypt", [0, 1])
def test_explorer_getrawtransaction(decrypt):

    if decrypt:
        assert isinstance(Explorer(network="ppc").getrawtransaction(
                          '34d19bf5a5c757d5bcbf83a91ad9bc04365c58a035a6bf728bce8013ad04c173', decrypt), dict)
    else:
        assert isinstance(Explorer(network="ppc").getrawtransaction(
                          '34d19bf5a5c757d5bcbf83a91ad9bc04365c58a035a6bf728bce8013ad04c173', decrypt), str)


def test_explorer_listtransactions():

    assert isinstance(Explorer(network="ppc").listtransactions(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), list)


def test_explorer_select_inputs():

    address = 'mvoSaPN8yTYWW7Tv3fVYTQnhkBuBWxpSP4'
    provider = Explorer(network='tppc')

    inputs = provider.select_inputs(address, 0.02)['utxos'][0]

    assert inputs.to_json() == {'scriptSig': {'asm': 'OP_DUP OP_HASH160 a7a826829741268ae2dd45942371000ea95d8524 OP_EQUALVERIFY OP_CHECKSIG',
                                'hex': '76a914a7a826829741268ae2dd45942371000ea95d852488ac'},
                                'sequence': '4294967295',
                                'txid': 'c637b4deb1ef552be42fd45a7cf8e4df0c7eeb5c4546d4343035ecf9669115ce',
                                'vout': 0
                                }
