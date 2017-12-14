import pytest
import pypeerassets as pa


def test_find_deck():

    provider = pa.Cryptoid(network="tppc")

    deck = pa.find_deck(provider, 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43', 1)

    assert deck.__dict__ == {'asset_specific_data': b'',
                             'fee': 0.0,
                             'id': 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43',
                             'issue_mode': 4,
                             'issue_time': 1488840533,
                             'issuer': 'msYThv5bf7KjhHT1Cj5D7Y1tofyhq9vhWM',
                             'name': 'hopium_v2',
                             'network': 'peercoin-testnet',
                             'number_of_decimals': 2,
                             'production': True,
                             'testnet': True,
                             'version': 1
                             }


def test_find_cards():

    provider = pa.Cryptoid(network="tppc")

    deck = pa.find_deck(provider, 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43', 1)

    cards = list(pa.find_card_transfers(provider, deck))

    assert cards
    assert isinstance(cards[0], pa.CardTransfer)
