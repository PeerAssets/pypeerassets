from decimal import Decimal

from pypeerassets.provider.cryptoid import Cryptoid


def test_cryptoid_is_testnet():

    cryptoid = Cryptoid(network="ppc")

    assert isinstance(cryptoid.is_testnet, bool)
    assert cryptoid.is_testnet is False


def test_crypotid_network():

    assert Cryptoid(network="ppc").network == "peercoin"


def test_cryptoid_getblockcount():

    assert isinstance(Cryptoid(network="ppc").getblockcount(), int)


def test_cryptoid_getblock():

    provider = Cryptoid(network="tppc")
    assert isinstance(provider.getblock('0000000429a1e623da44a7430b9d9ae377bc2da203043c444c313b2d4390eba2'), dict)


def test_cryptoid_get_block_hash():

    assert isinstance(Cryptoid(network="ppc").getblockhash(3378), str)


def test_cryptoid_getdifficulty():

    difficulty = Cryptoid(network="ppc").getdifficulty()
    assert isinstance(difficulty["proof-of-stake"], float)


def test_cryptoid_getbalance():

    assert isinstance(Cryptoid(network="ppc").getbalance(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), Decimal)


def test_cryptoid_getreceivedbyaddress():

    assert isinstance(Cryptoid(network="ppc").getreceivedbyaddress(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), Decimal)


def test_cryptoid_listunspent():

    assert isinstance(Cryptoid(network="ppc").listunspent(
                      'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw'), list)


def test_cryptoid_getrawtransaction():

    assert isinstance(Cryptoid(network="ppc").getrawtransaction(
                      '34d19bf5a5c757d5bcbf83a91ad9bc04365c58a035a6bf728bce8013ad04c173', 1), dict)


def test_cryptoid_listtransactions():

    assert isinstance(Cryptoid(network="tppc").listtransactions(
                      'msPLoMcHpn6Y28pPKwATG411m5X7Vodu3m'), list)


def test_cryptoid_select_inputs():

    address = 'mvoSaPN8yTYWW7Tv3fVYTQnhkBuBWxpSP4'
    provider = Cryptoid(network='tppc')

    inputs = provider.select_inputs(address, 0.02)['utxos'][0]

    assert inputs.to_json() == {'scriptSig': {'asm': 'OP_DUP OP_HASH160 a7a826829741268ae2dd45942371000ea95d8524 OP_EQUALVERIFY OP_CHECKSIG',
                                'hex': '76a914a7a826829741268ae2dd45942371000ea95d852488ac'},
                                'sequence': '4294967295',
                                'txid': 'c637b4deb1ef552be42fd45a7cf8e4df0c7eeb5c4546d4343035ecf9669115ce',
                                'vout': 0
                                }
