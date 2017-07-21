import pytest
from pypeerassets import Mintr


def test_mintr_getinfo():

    assert Mintr().getinfo() == {"testnet": False}


def test_mintr_network():

    assert Mintr().network == "ppc"


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

    assert Mintr().getrawtransaction("147c4daf47293fb670efd97dd7f9f6e964f515e6478e0cc3a668e4330f12ad6f") == tx


def test_mintr_listtransaction():

    assert isinstance(Mintr().listtransactions("PPchatrw5hV1y3JUU2kxyL4LQccprbp8FX"), list)
