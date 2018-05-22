import pytest

from pypeerassets.provider.holytransaction import Holy


def test_holy_is_testnet():

    assert Holy(network="peercoin-testnet").is_testnet is True


def test_holy_network():

    assert Holy(network="ppc").network == "peercoin"


def test_holy_getdifficulty():

    get_diff = Holy(network="peercoin").getdifficulty()

    assert isinstance(get_diff, dict)
    assert sorted(get_diff.keys()) == ['proof-of-stake', 'proof-of-work', 'search-interval']


def test_holy_getblockcount():

    assert isinstance(Holy(network="peercoin").getblockcount(), int)


def test_holy_getblockhash():

    get_blockhash = Holy(network="peercoin").getblockhash(313639)

    assert isinstance(get_blockhash, str)
    assert get_blockhash == 'be48bcf5155b4650d75d600bf1e9f37a5a049c2905542c6ced43ec0cb57673e8'


def test_holy_getblock():

    getblock = Holy(network="peercoin").getblock("be48bcf5155b4650d75d600bf1e9f37a5a049c2905542c6ced43ec0cb57673e8")

    assert isinstance(getblock, dict)
    assert sorted(getblock.keys()) == ['bits', 'difficulty', 'entropybit',
                                       'flags', 'hash', 'height',
                                       'merkleroot', 'mint', 'modifier',
                                       'modifierchecksum', 'nextblockhash',
                                       'nonce', 'previousblockhash',
                                       'proofhash', 'size', 'time',
                                       'tx', 'version'
                                       ]


@pytest.mark.parametrize("decrypt", [0, 1])
def test_holy_getrawtransaction(decrypt):

    getrawtransaction = Holy(network="peercoin").getrawtransaction('e4c8ebffe416836faa8f35ae9bc630cc2ac706faebc4e40d5556a755024a3689', decrypt)

    if decrypt:
        assert isinstance(getrawtransaction, dict)
        assert sorted(getrawtransaction.keys()) == ['blockhash',
                                                    'blocktime',
                                                    'confirmations',
                                                    'hex',
                                                    'locktime',
                                                    'time',
                                                    'txid',
                                                    'version',
                                                    'vin',
                                                    'vout']
    else:
        assert isinstance(getrawtransaction, bytes)


def test_holy_getaddress():

    getaddress = Holy(network="peercoin").getaddress('PXBf64T4gqKcn7Kruw75X8V5yeci34HG92')

    assert isinstance(getaddress, dict)
    assert sorted(getaddress.keys()) == ['address', 'balance', 'last_txs', 'received', 'sent']


def test_holy_getbalance():

    assert isinstance(Holy(network="peercoin").getbalance('PXBf64T4gqKcn7Kruw75X8V5yeci34HG92'), float)


def test_holy_listtransactions():

    assert isinstance(Holy(network="peercoin").listtransactions("PXBf64T4gqKcn7Kruw75X8V5yeci34HG92"), list)
