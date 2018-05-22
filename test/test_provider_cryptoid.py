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

    assert isinstance(Cryptoid(network="ppc").getdifficulty(), float)


def test_cryptoid_getbalance():

    assert isinstance(Cryptoid(network="ppc").getbalance(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), float)


def test_cryptoid_getreceivedbyaddress():

    assert isinstance(Cryptoid(network="ppc").getreceivedbyaddress(
                      'PHvDhfz1dGyPbZZ3Qnp56y92zmy98sncZT'), float)


def test_cryptoid_listunspent():

    assert isinstance(Cryptoid(network="ppc").listunspent(
                      'PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw'), list)


def test_cryptoid_getrawtransaction():

    assert isinstance(Cryptoid(network="ppc").getrawtransaction(
                      '34d19bf5a5c757d5bcbf83a91ad9bc04365c58a035a6bf728bce8013ad04c173'), dict)


def test_cryptoid_listtransactions():

    assert isinstance(Cryptoid(network="tppc").listtransactions(
                      'msPLoMcHpn6Y28pPKwATG411m5X7Vodu3m'), list)
