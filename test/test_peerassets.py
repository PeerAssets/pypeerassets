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
    with pytest.raises(pa.exceptions.EmptyP2THDirectory):
        assert isinstance(next(cards), pa.CardTransfer)


def test_deck_spawn():

    provider = pa.Explorer(network='tppc')
    inputs = provider.select_inputs("mthKQHpr7zUbMvLcj8GHs33mVcf91DtN6L", 0.02)
    change_address = "mthKQHpr7zUbMvLcj8GHs33mVcf91DtN6L"
    deck = pa.Deck(name="just-testing.", number_of_decimals=1, issue_mode=1,
                   network='tppc', production=True, version=1)

    deck_spawn = pa.deck_spawn(provider, deck, inputs, change_address)

    assert isinstance(deck_spawn, pa.Transaction)


def test_card_transfer():

    provider = pa.Explorer(network='tppc')
    address = "mthKQHpr7zUbMvLcj8GHs33mVcf91DtN6L"
    inputs = provider.select_inputs(address, 0.02)
    change_address = address
    deck = pa.find_deck(provider, '078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915', 1, True)
    card = pa.CardTransfer(deck=deck,
                           receiver=['n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj',
                                     'n422r6tcJ5eofjsmRvF6TcBMigmGbY5P7E'],
                           amount=[1, 2]
                           )

    card_transfer = pa.card_transfer(provider, card, inputs, change_address)

    assert isinstance(card_transfer, pa.Transaction)
