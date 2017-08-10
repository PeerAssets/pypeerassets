import pytest
from pypeerassets import Mintr, Holy, Cryptoid


def test_mintr_getinfo():

    assert Mintr().getinfo() == {"testnet": False}


def test_mintr_network():

    assert Mintr().network == "peercoin"


def test_mintr_getrawtransaction():

    tx = {'avgcoindaysdestroyed': '1.033657406',
          'blocktime': '1484062161',
          'coindaysdestroyed': '17.768570826',
          'fee': '0.01',
          'numvin': '1',
          'numvout': '2',
          'tx_hash': '147c4daf47293fb670efd97dd7f9f6e964f515e6478e0cc3a668e4330f12ad6f',
          'valuein': '17.19',
          'valueout': '17.18',
          'vin': [{'address': 'PWbafEjfujD1UhexfrCU5oc3K4kPUrzkun',
                   'asm': '3045022100fb960849454c0b6602e04229a33a0c363468e5053d991ac6f53e323457866fbf022060b6ed2abd3a6984234d5df7291354c6678d02bf10108c555d85411077e37c1701 022e00c25330a36205bf59ea354f0c51acf18ea7b051458fc84a8824ac1f8d235e',
                   'avgcoindaysdestroyed': '1.033657406',
                   'coinbase': '',
                   'coindaysdestroyed': '17.768570826',
                   'hex': '483045022100fb960849454c0b6602e04229a33a0c363468e5053d991ac6f53e323457866fbf022060b6ed2abd3a6984234d5df7291354c6678d02bf10108c555d85411077e37c170121022e00c25330a36205bf59ea354f0c51acf18ea7b051458fc84a8824ac1f8d235e',
                   'output_txid': 'e7b4ba687bfd3882ba529dee122b965f995c09fd2521dbb25209f8cd5d4d587c',
                   'sequence': '4294967295',
                   'value': '17.19',
                   'vout': '0'}],
          'vout': [{'n': '0',
                    'scriptPubKey': {'address': ['PEmVoMtgFe1WJEXMwhASUfn9UTeupsoGPR'],
                                     'asm': 'OP_DUP OP_HASH160 43c47a626ddeaa9c7e587c510f91d4077a364605 OP_EQUALVERIFY OP_CHECKSIG',
                                     'hex': '76a91443c47a626ddeaa9c7e587c510f91d4077a36460588ac',
                                     'reqSigs': '0',
                                     'type': ''},
                    'value': '16.18'},
                    {'n': '1',
                     'scriptPubKey': {'address': ['PPchatrw5hV1y3JUU2kxyL4LQccprbp8FX'],
                                      'asm': 'OP_DUP OP_HASH160 a4d3b442a56f173858ede1a5bb18cd6ce3b05558 OP_EQUALVERIFY OP_CHECKSIG',
                                      'hex': '76a914a4d3b442a56f173858ede1a5bb18cd6ce3b0555888ac',
                                      'reqSigs': '0',
                                      'type': ''},
                                      'value': '1'}
                                      ]
                                    }

    assert isinstance(Mintr().getrawtransaction("147c4daf47293fb670efd97dd7f9f6e964f515e6478e0cc3a668e4330f12ad6f"), dict)


def test_mintr_getblock():

    assert isinstance(Mintr().getblock('be48bcf5155b4650d75d600bf1e9f37a5a049c2905542c6ced43ec0cb57673e8'), dict)


def test_mintr_listtransaction():

    assert isinstance(Mintr().listtransactions("PPchatrw5hV1y3JUU2kxyL4LQccprbp8FX"), list)


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
