from typing import Generator

import pytest

from pypeerassets import (
    Cryptoid,
    Deck,
    Explorer,
    Mintr,
    RpcNode,
    find_deck,
)
from pypeerassets.exceptions import *
from pypeerassets.paproto_pb2 import DeckSpawn
from pypeerassets.pautils import *
from pypeerassets.protocol import IssueMode, CardTransfer
from pypeerassets.pa_constants import param_query


@pytest.mark.xfail
def test_load_p2th_privkeys_into_local_node():

    provider = RpcNode(testnet=True)
    load_p2th_privkeys_into_local_node(provider=provider)


@pytest.mark.parametrize("prov", ["explorer", "mintr", 'cryptoid'])
def test_find_tx_sender(prov):

    if prov == "explorer":
        provider = Explorer(network="peercoin")
        rawtx = provider.getrawtransaction("397bda2f5e6608c872a663b2e5482d95db8ecfad00757823f0f12caa45a213a6", 1)
        assert find_tx_sender(provider, rawtx) == 'PNHGzKupyvo2YZVb1CTdRxtCGBB5ykgiug'

    if prov == "mintr":
        provider = Mintr()
        rawtx = provider.getrawtransaction("397bda2f5e6608c872a663b2e5482d95db8ecfad00757823f0f12caa45a213a6", 1)
        assert find_tx_sender(provider, rawtx) == 'PNHGzKupyvo2YZVb1CTdRxtCGBB5ykgiug'

    if prov == "cryptoid":
        provider = Cryptoid(network="peercoin")
        rawtx = provider.getrawtransaction("397bda2f5e6608c872a663b2e5482d95db8ecfad00757823f0f12caa45a213a6", 1)
        assert find_tx_sender(provider, rawtx) == 'PNHGzKupyvo2YZVb1CTdRxtCGBB5ykgiug'

@pytest.mark.parametrize("prov", ["explorer", "mintr", "cryptoid"])
def test_find_deck_spawns(prov):

    if prov == "explorer":
        provider = Explorer(network="peercoin")

    if prov == "mintr":
        provider = Mintr()

    if prov == "cryptoid":
        provider = Cryptoid(network="peercoin")

    assert isinstance(find_deck_spawns(provider), Generator)


@pytest.mark.parametrize("prov", ["rpc", "explorer", "mintr"])
def test_tx_serialization_order(prov):

    if prov == "explorer":
        provider = Explorer(network="peercoin-testnet")
        assert tx_serialization_order(provider,
                                      txid="f968702bcedc107959aae2c2b1a1becdccbfe7e5a32b460b2c13c1adaa33d541", blockhash="e234d2ef69f7cd1e7ee489546b39314cc838763b4e32438106cba657d9749f2f") == 1

    if prov == "mintr":
        provider = Mintr()
        assert tx_serialization_order(provider,
                                      txid="6f9c76f5e2d188c8d4e8411a89dd152ca94e6b1756aec6c4d12fcbf0450970f7", blockhash="13ea431cb818628d762f224fb3fa957ecdbab661d190d28aedef8449e007f207") == 0


    try:
        if prov == "rpc":
            provider = RpcNode(testnet=True)
            assert tx_serialization_order(provider,
                                          txid="f968702bcedc107959aae2c2b1a1becdccbfe7e5a32b460b2c13c1adaa33d541", blockhash="e234d2ef69f7cd1e7ee489546b39314cc838763b4e32438106cba657d9749f2f") == 1

    except:
        print("No RpcNode avaliable.")


def test_read_tx_opreturn():

    rawtx = {'blockhash': 'aef46dc82bcc9b40ff0c05e2498c4f85db7e273fc6f7e656acbcd1c8e0c93356',
             'blocktime': 1489426035,
             'confirmations': 23696,
             'hex': '010000004ad4c6580107c7390516448a1b03e7fc2c55e2e816aa0e0745e4e5089393ee1d0fbf0ad0fb020000006c49304602210099d36b8c36f29e2d7c423ebb68ef804744c3681e81ea2db7f02ea930c4aaa984022100f2d7e044e1b4034a5edb65f38fd4451ed11fe43a240eaacb58cb951de842bc190121029becbd50edbb8fee8fc1227112e6c8a6b6ead69c3660b560e5eab22c2fe8f976ffffffff0310270000000000001976a9141e667ee94ea8e62c63fe59a0269bb3c091c86ca388ac0000000000000000196a170801120f736978746f5f726f6472696775657a18052004601f0d00000000001976a91456a0a01afba6687e98e5e61b434d45a337f2cd2588ac00000000',
             'locktime': 0,
             'time': 1489425482,
             'txid': '643dccd585211766fc03f71e92fbf299cfc2bdbf3f2cae0ad85adec3141069f3',
             'version': 1,
             'vin': [{'scriptSig': {'asm': '304602210099d36b8c36f29e2d7c423ebb68ef804744c3681e81ea2db7f02ea930c4aaa984022100f2d7e044e1b4034a5edb65f38fd4451ed11fe43a240eaacb58cb951de842bc1901 029becbd50edbb8fee8fc1227112e6c8a6b6ead69c3660b560e5eab22c2fe8f976',
                      'hex': '49304602210099d36b8c36f29e2d7c423ebb68ef804744c3681e81ea2db7f02ea930c4aaa984022100f2d7e044e1b4034a5edb65f38fd4451ed11fe43a240eaacb58cb951de842bc190121029becbd50edbb8fee8fc1227112e6c8a6b6ead69c3660b560e5eab22c2fe8f976'},
             'sequence': 4294967295,
             'txid': 'fbd00abf0f1dee939308e5e445070eaa16e8e2552cfce7031b8a44160539c707',
             'vout': 2}],
             'vout': [{'n': 0,
             'scriptPubKey': {'addresses': ['miHhMLaMWubq4Wx6SdTEqZcUHEGp8RKMZt'],
                'asm': 'OP_DUP OP_HASH160 1e667ee94ea8e62c63fe59a0269bb3c091c86ca3 OP_EQUALVERIFY OP_CHECKSIG',
                'hex': '76a9141e667ee94ea8e62c63fe59a0269bb3c091c86ca388ac',
                'reqSigs': 1,
                'type': 'pubkeyhash'},
             'value': 0.01},
             {'n': 1,
             'scriptPubKey': {'asm': 'OP_RETURN 0801120f736978746f5f726f6472696775657a18052004',
                'hex': '6a170801120f736978746f5f726f6472696775657a18052004',
                'type': 'nulldata'},
             'value': 0},
             {'n': 2,
             'scriptPubKey': {'addresses': ['moQzpzzcCYZMnAz224EY4att5A9psxN8X2'],
                'asm': 'OP_DUP OP_HASH160 56a0a01afba6687e98e5e61b434d45a337f2cd25 OP_EQUALVERIFY OP_CHECKSIG',
                'hex': '76a91456a0a01afba6687e98e5e61b434d45a337f2cd2588ac',
                'reqSigs': 1,
                'type': 'pubkeyhash'},
             'value': 0.86}]}

    assert isinstance(read_tx_opreturn(rawtx), bytes)
    assert read_tx_opreturn(rawtx) == b'\x08\x01\x12\x0fsixto_rodriguez\x18\x05 \x04'


def generate_dummy_deck():

    return Deck(
        name="decky",
        number_of_decimals=2,
        issue_mode=IssueMode.SINGLET.value,
        network="ppc",
        production=True,
        version=1,
        asset_specific_data="just testing.",
    )


def test_deck_issue_mode():
    '''test enum to issue_mode conversion'''

    deck_meta = DeckSpawn()
    deck_meta.issue_mode = 3

    assert isinstance(deck_issue_mode(deck_meta), Generator)
    assert list(deck_issue_mode(deck_meta)) == ['CUSTOM', 'ONCE']

    # Check that we handle NONE mode correctly.
    deck_meta.issue_mode = 0
    assert list(deck_issue_mode(deck_meta)) == ['NONE']


def test_issue_mode_to_enum():
    '''test issue mode to enum conversion'''

    deck = generate_dummy_deck().metainfo_to_protobuf
    deck_meta = DeckSpawn()
    deck_meta.ParseFromString(deck)

    assert isinstance(issue_mode_to_enum(deck_meta,
                      ["CUSTOM", "SINGLET"]), int)


def test_parse_deckspawn_metainfo():
    '''tests if loading of deck parameteres from protobuf works as it should.'''

    string = b'\x08\x01\x12\x0cmy_test_deck\x18\x03 \x02'
    assert parse_deckspawn_metainfo(string, 1) == {'issue_mode': IssueMode.ONCE.value,
                                                   'name': 'my_test_deck',
                                                   'number_of_decimals': 3,
                                                   'version': 1,
                                                   'asset_specific_data': b''
                                                  }

    string = b'\x08\x01\x18\x05 \x04' # without deck name
    with pytest.raises(InvalidDeckMetainfo):
        parse_deckspawn_metainfo(string, 1)


def test_validate_deckspawn_p2th():
    '''test deckspawn p2th validation'''

    provider = Explorer(network="peercoin-testnet")
    p2th = param_query('peercoin-testnet').P2TH_addr
    raw_tx = provider.getrawtransaction('643dccd585211766fc03f71e92fbf299cfc2bdbf3f2cae0ad85adec3141069f3', 1,)

    assert validate_deckspawn_p2th(provider, raw_tx, p2th)


@pytest.mark.xfail
def test_load_deck_p2th_into_local_node():

    provider = RpcNode(testnet=True)
    deck = generate_dummy_deck()
    load_deck_p2th_into_local_node(provider, deck)


def test_validate_card_transfer_p2th():

    provider = Cryptoid(network="peercoin-testnet")
    deck = find_deck(provider, "643dccd585211766fc03f71e92fbf299cfc2bdbf3f2cae0ad85adec3141069f3", 1)
    raw_tx = provider.getrawtransaction("809c506bc3add9e46a4d3a65348426688545213da5fb5b524acd380f2cdaf3cc", 1)

    validate_card_transfer_p2th(deck, raw_tx)


def test_parse_card_transfer_metainfo():

    card = b'\x08\x01\x12\n\xd0\xd2=\x80\x89z\xee\x83\xb8\x01\x18\x05'
    res = parse_card_transfer_metainfo(card, 1)

    assert isinstance(res, dict)


def test_postprocess_card():

    provider = Explorer(network="peercoin-testnet")
    deck = find_deck(provider, "643dccd585211766fc03f71e92fbf299cfc2bdbf3f2cae0ad85adec3141069f3", 1)
    raw_tx = provider.getrawtransaction('809c506bc3add9e46a4d3a65348426688545213da5fb5b524acd380f2cdaf3cc', 1)
    vout = raw_tx["vout"]
    blockseq = tx_serialization_order(provider, raw_tx["blockhash"], raw_tx["txid"])
    blocknum = provider.getblock(raw_tx["blockhash"])["height"]
    sender = 'moQzpzzcCYZMnAz224EY4att5A9psxN8X2'
    card_transfer = CardTransfer(
                    deck=deck,
                    receiver=["n4KuTR5CzyQTbrpwbAKEdTfJERKmtHWWgr"],
                    amount=[1],
                    version=1,
                    )

    card = postprocess_card(card_metainfo=card_transfer.metainfo_to_dict, 
                            raw_tx=raw_tx,
                            sender=sender, 
                            vout=vout,
                            blockseq=blockseq,
                            blocknum=blocknum,
                            tx_confirmations=raw_tx['confirmations'],
                            deck=deck)

    assert isinstance(card, list)


def test_amount_to_exponent():

    assert isinstance(amount_to_exponent(88.99, 3), int)
    assert amount_to_exponent(88.99, 3) == 88990


def test_exponent_to_amount():

    assert isinstance(exponent_to_amount(10, 6), float)
    assert exponent_to_amount(10, 3) == 0.01
