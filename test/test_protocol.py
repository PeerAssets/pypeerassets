import pytest
from pypeerassets import protocol


def test_deck_object():
    '''test creation of deck objects'''

    deck = protocol.Deck(name="decky", number_of_decimals=2, issue_mode="MULTI",
                         network="ppc", production=True,
                         asset_specific_data="Just testing.")

    assert deck.__dict__ == {'asset_id': None,
                             'asset_specific_data': 'Just testing.',
                             'issue_mode': 'MULTI',
                             'issue_time': None,
                             'issuer': '',
                             'name': 'decky',
                             'network': 'ppc',
                             'number_of_decimals': 2,
                             'production': True,
                             'testnet': False,
                             'version': 1
                             }

    assert deck.metainfo_to_protobuf == b'\x08\x01\x12\x05decky\x18\x02 \x04*\rJust testing.'

    assert deck.metainfo_to_dict == {'issue_mode': 'MULTI', 'name': 'decky', 'number_of_decimals': 2, 'version': 1}


def test_card_transfer_object():

    deck = protocol.Deck(name="decky", number_of_decimals=2, issue_mode="MULTI",
                         network="ppc", production=True,
                         asset_specific_data="Just testing.")


    card_transfer = protocol.CardTransfer(deck=deck,
                                          receiver=["PDZ9MPBPPjtT6qdJm98PhLVY9gNtFUoSLT"],
                                          amount=[1], version=1)

    assert card_transfer.metainfo_to_protobuf == b'\x08\x01\x12\x01\x01\x18\x02'

    assert card_transfer.__dict__ == {'amount': [1],
                                      'asset_specific_data': '',
                                      'blockhash': 0,
                                      'blocknum': 0,
                                      'blockseq': 0,
                                      'cardseq': 0,
                                      'deck_id': None,
                                      'number_of_decimals': 2,
                                      'receiver': ['PDZ9MPBPPjtT6qdJm98PhLVY9gNtFUoSLT'],
                                      'sender': None,
                                      'timestamp': 0,
                                      'txid': None,
                                      'type': 'CardTransfer',
                                      'version': 1
                                      }
