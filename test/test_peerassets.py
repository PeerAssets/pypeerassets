import pytest
import pypeerassets as pa


def test_find_deck():

    provider = pa.Cryptoid(network="tppc")

    deck = pa.find_deck(provider, 'b6a95f94fef093ee9009b04a09ecb9cb5cba20ab6f13fe0926aeb27b8671df43', 1)

    assert deck.__dict__ == {'asset_specific_data': b'',
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

    cards = pa.find_card_transfers(provider, deck)

    assert cards
    assert isinstance(next(cards), pa.CardTransfer)


def test_deck_spawn():

    provider = pa.Explorer(network='tppc')
    key = pa.Kutil(network='tppc', privkey=bytearray.fromhex('f76e9331abd2cf811375d7192dfcb39d507bf16e58cfe72b0f2a5d5195172ab9'))
    inputs = provider.select_inputs(key.address, 0.02)
    change_address = key.address
    deck = pa.Deck(name="just-testing.", number_of_decimals=1, issue_mode=1,
                   network='peercoin-testnet', production=True, version=1)

    deck_spawn = pa.deck_spawn(provider, key, deck, inputs, change_address)

    assert isinstance(deck_spawn, pa.Transaction)
