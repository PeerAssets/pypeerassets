from typing import Generator

import pytest

from pypeerassets import (
    Cryptoid,
    Deck,
    Explorer,
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


@pytest.mark.parametrize("prov", ["explorer", "cryptoid"])
def test_find_tx_sender(prov):

    if prov == "explorer":
        provider = Explorer(network="peercoin")
        rawtx = provider.getrawtransaction("397bda2f5e6608c872a663b2e5482d95db8ecfad00757823f0f12caa45a213a6", 1)
        assert find_tx_sender(provider, rawtx) == 'PNHGzKupyvo2YZVb1CTdRxtCGBB5ykgiug'

    if prov == "cryptoid":
        provider = Cryptoid(network="peercoin")
        rawtx = provider.getrawtransaction("397bda2f5e6608c872a663b2e5482d95db8ecfad00757823f0f12caa45a213a6", 1)
        assert find_tx_sender(provider, rawtx) == 'PNHGzKupyvo2YZVb1CTdRxtCGBB5ykgiug'


@pytest.mark.parametrize("prov", ["explorer", "cryptoid"])
def test_find_deck_spawns(prov):

    if prov == "explorer":
        provider = Explorer(network="peercoin")

    if prov == "cryptoid":
        provider = Cryptoid(network="peercoin")

    assert isinstance(find_deck_spawns(provider), Generator)


@pytest.mark.parametrize("prov", ["rpc", "explorer"])
def test_tx_serialization_order(prov):

    if prov == "explorer":
        provider = Explorer(network="peercoin-testnet")
        assert tx_serialization_order(provider,
                                      txid="f968702bcedc107959aae2c2b1a1becdccbfe7e5a32b460b2c13c1adaa33d541", blockhash="e234d2ef69f7cd1e7ee489546b39314cc838763b4e32438106cba657d9749f2f") == 1

    try:
        if prov == "rpc":
            provider = RpcNode(testnet=True)
            assert tx_serialization_order(provider,
                                          txid="f968702bcedc107959aae2c2b1a1becdccbfe7e5a32b460b2c13c1adaa33d541", blockhash="e234d2ef69f7cd1e7ee489546b39314cc838763b4e32438106cba657d9749f2f") == 1

    except:
        print("No RpcNode avaliable.")


def test_read_tx_opreturn():

    vout = [{'n': 0,
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
              'value': 0}
             ]

    assert isinstance(read_tx_opreturn(vout[1]), bytes)
    assert read_tx_opreturn(vout[1]) == b'\x08\x01\x12\x0fsixto_rodriguez\x18\x05 \x04'


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

    validate_card_transfer_p2th(deck, raw_tx['vout'][0])


def test_parse_card_transfer_metainfo():

    card = b'\x08\x01\x12\n\xd0\xd2=\x80\x89z\xee\x83\xb8\x01\x18\x05'
    res = parse_card_transfer_metainfo(card, 1)

    assert isinstance(res, dict)


def test_amount_to_exponent():

    assert isinstance(amount_to_exponent(88.99, 3), int)
    assert amount_to_exponent(88.99, 3) == 88990


def test_exponent_to_amount():

    assert isinstance(exponent_to_amount(10, 6), float)
    assert exponent_to_amount(10, 3) == 0.01
