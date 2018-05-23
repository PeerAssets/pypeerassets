from pypeerassets.protocol import CardTransfer, Deck, IssueMode


def test_deck_object():
    '''test creation of deck objects'''

    deck = Deck(
        name="decky",
        number_of_decimals=2,
        issue_mode=IssueMode.MULTI.value,
        network="ppc",
        production=True,
        version=1,
        asset_specific_data="Just testing.",
    )

    assert deck.__dict__ == {'id': None,
                             'asset_specific_data': 'Just testing.',
                             'issue_mode': IssueMode.MULTI.value,
                             'issue_time': None,
                             'issuer': '',
                             'name': 'decky',
                             'network': 'ppc',
                             'number_of_decimals': 2,
                             'production': True,
                             'testnet': False,
                             'version': 1,
                            }

    assert deck.metainfo_to_protobuf == b'\x08\x01\x12\x05decky\x18\x02 \x04*\rJust testing.'

    assert deck.metainfo_to_dict == {'issue_mode': IssueMode.MULTI.value,
                                     'name': 'decky',
                                     'number_of_decimals': 2,
                                     'version': 1,
                                     'asset_specific_data': 'Just testing.',
                                    }


def test_card_transfer_object():

    deck = Deck(
        name="decky",
        number_of_decimals=2,
        issue_mode=IssueMode.MULTI.value,
        network="ppc",
        production=True,
        version=1,
        asset_specific_data="Just testing.",
    )

    card_transfer = CardTransfer(
        deck=deck,
        receiver=["PDZ9MPBPPjtT6qdJm98PhLVY9gNtFUoSLT"],
        amount=[1],
        version=1,
    )

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
