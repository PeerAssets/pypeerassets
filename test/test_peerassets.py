import pytest
import pypeerassets as pa
from pypeerassets.__main__ import find_card_bundles, get_card_transfer
from pypeerassets.protocol import CardBundle, CardTransfer
from pypeerassets.provider import Explorer, Cryptoid
from btcpy.structs.transaction import MutableTransaction
from pypeerassets.transactions import Transaction


@pytest.mark.parametrize("prov", [Explorer, Cryptoid])
def test_find_deck(prov):

    provider = prov(network="tppc")

    deck = pa.find_deck(provider, 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43', 1)

    deck.tx_confirmations = 100  # make it deterministic

    assert deck.to_json() == {'asset_specific_data': b'',
                              'id': 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43',
                              'issue_mode': 4,
                              'issue_time': 1488840533,
                              'issuer': 'msYThv5bf7KjhHT1Cj5D7Y1tofyhq9vhWM',
                              'name': 'hopium_v2',
                              'network': 'peercoin-testnet',
                              'number_of_decimals': 2,
                              'production': True,
                              'version': 1,
                              'tx_confirmations': 100,
                              'p2th_wif': 'cThmj6Qu6aTUeA5f4FoNJTsBA8K6ZjhXbZkwsqcmv94xjWiCBr5d'
                              }


def test_find_card_bundles():

    provider = Explorer(network="tppc")
    deck = pa.find_deck(provider, 'adc6d888508ebfcad5c182df4ae94553bae6287735d76b8d64b3de8d29fc2b5b', 1)

    bundles = find_card_bundles(provider, deck)

    assert bundles
    assert isinstance(next(bundles), CardBundle)


@pytest.mark.parametrize("prov", [Explorer, Cryptoid])
def test_get_card_bundles(prov):

    provider = prov(network="tppc")

    deck = pa.find_deck(provider, 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43', 1)

    bundles = pa.get_card_bundles(provider, deck)

    assert bundles
    assert isinstance(list(next(bundles))[0], pa.CardTransfer)


def test_get_card_transfer():
    '''test finding a single card tranfer'''

    provider = Explorer(network="tppc")

    deck = pa.find_deck(provider, '98694bb54fafe315051d2a8f1f5ea4c0050947741ced184a5f33bf4a0081a0bb', 1, True)

    card = list(get_card_transfer(provider, deck, 'e04fb602bd9d9c33d1d1af8bb680108057c2ae37ea987cc15295cc6fc4fd8d97'))

    assert isinstance(card[0], CardTransfer)


@pytest.mark.parametrize("prov", [Explorer, Cryptoid])
def test_find_all_valid_cards(prov):

    provider = prov(network="tppc")

    deck = pa.find_deck(provider, 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43', 1)

    cards = pa.find_all_valid_cards(provider, deck)

    assert cards
    assert isinstance(next(cards), pa.CardTransfer)


def test_deck_spawn():

    provider = Explorer(network='tppc')
    inputs = provider.select_inputs("mthKQHpr7zUbMvLcj8GHs33mVcf91DtN6L", 0.02)
    change_address = "mthKQHpr7zUbMvLcj8GHs33mVcf91DtN6L"
    deck = pa.Deck(name="just-testing.", number_of_decimals=1, issue_mode=1,
                   network='tppc', production=True, version=1,
                   asset_specific_data='https://talk.peercoin.net/')

    deck_spawn = pa.deck_spawn(provider, deck, inputs, change_address)

    assert isinstance(deck_spawn, MutableTransaction)


def test_card_transfer():

    provider = Explorer(network='tppc')
    address = "mthKQHpr7zUbMvLcj8GHs33mVcf91DtN6L"
    inputs = provider.select_inputs(address, 0.02)
    change_address = address
    deck = pa.find_deck(provider,
                         '078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915',
                         1, True)
    card = pa.CardTransfer(deck=deck,
                           receiver=['n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj',
                                     'n422r6tcJ5eofjsmRvF6TcBMigmGbY5P7E'],
                           amount=[1, 2]
                           )

    card_transfer = pa.card_transfer(provider, card, inputs, change_address,
                                     locktime=300000)

    assert isinstance(card_transfer, Transaction)
