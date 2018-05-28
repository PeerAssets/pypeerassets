import pytest
import random
import itertools
from pypeerassets import Kutil
from pypeerassets.protocol import (CardTransfer, Deck, IssueMode,
                                   validate_card_issue_modes, DeckState)


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
                             'confirms': None,
                             'issuer': '',
                             'name': 'decky',
                             'network': 'ppc',
                             'number_of_decimals': 2,
                             'production': True,
                             'testnet': False,
                             'version': 1
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
                                      'asset_specific_data': None,
                                      'blockhash': 0,
                                      'blocknum': 0,
                                      'blockseq': 0,
                                      'cardseq': 0,
                                      'confirms': 0,
                                      'deck_id': None,
                                      'number_of_decimals': 2,
                                      'receiver': ['PDZ9MPBPPjtT6qdJm98PhLVY9gNtFUoSLT'],
                                      'sender': None,
                                      'timestamp': 0,
                                      'txid': None,
                                      'type': 'CardTransfer',
                                      'version': 1,
                                      'deck_p2th': None
                                      }


@pytest.mark.parametrize("combo", [IssueMode.ONCE, IssueMode.MULTI, IssueMode.MONO])
def test_issue_mode_combos(combo):

    base_issue_mode = IssueMode.CUSTOM

    if combo == IssueMode.ONCE:
        assert base_issue_mode.value + combo.value == 3

    if combo == IssueMode.MULTI:
        assert base_issue_mode.value + combo.value == 5

    if combo == IssueMode.MONO:
        assert base_issue_mode.value + combo.value == 9


def few_random_cards(deck: Deck, n: int, card_type: str='random',
                     amount: int=None) -> list:
    '''returns <n> randomly generated cards'''

    types = ['CardIssue', 'CardBurn', 'CardTransfer']

    cards = [CardTransfer(
        deck=deck,
        receiver=[Kutil(network='tppc').address],
        amount=[random.randint(1, 100)],
        ) for i in range(n)]

    if card_type == 'transfer':
        for i in cards:
            i.__setattr__('type', 'CardTransfer')

    if card_type == 'random':
        for i in cards:
            i.__setattr__('type', random.choice(types))

    if card_type == 'issue':
        for i in cards:
            i.__setattr__('type', 'CardIssue')

    if card_type == 'burn':
        for i in cards:
            i.__setattr__('type', 'CardBurn')

    if amount:  # if there is strict requirement for amount to be <int>
        for i in cards:
            i.amount = [amount]

    return cards


def test_validate_multi_card_issue_mode():
    '''test card filtering against MULTI deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=2,
        issue_mode=IssueMode.MULTI.value,
        network="tppc",
        production=True,
        version=1,
        )

    cards = few_random_cards(deck, 4, 'issue')

    assert len(validate_card_issue_modes(deck.issue_mode, cards)) == 4


def test_validate_once_card_issue_mode():
    '''test card filtering against ONCE deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=2,
        issue_mode=IssueMode.ONCE.value,
        network="tppc",
        production=True,
        version=1,
        )

    cards = few_random_cards(deck, 8, 'issue')

    assert len(validate_card_issue_modes(deck.issue_mode, cards)) == 1


def test_validate_none_card_issue_mode():
    '''test card filtering against None deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=IssueMode.NONE.value,
        network="tppc",
        production=True,
        version=1,
        )

    cards = few_random_cards(deck, 8, 'issue')

    assert len(validate_card_issue_modes(deck.issue_mode, cards)) == 0


def test_validate_unflushable_card_issue_mode():
    '''test card filtering against None deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=IssueMode.UNFLUSHABLE.value,
        network="tppc",
        production=True,
        version=1,
        )

    cards_issues = few_random_cards(deck, 8, 'issue')
    random_cards = few_random_cards(deck, 16, 'transfer')

    assert len(validate_card_issue_modes(deck.issue_mode, cards_issues + random_cards)) == 8


def test_validate_mono_card_issue_mode():
    '''test card filtering against MONO deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=IssueMode.MONO.value,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 10, 'issue', 1)
    other = few_random_cards(deck, 9, 'transfer', 1)
    invalid = few_random_cards(deck, 9, 'transfer', 2)

    assert len(validate_card_issue_modes(deck.issue_mode, issues + other + invalid)) == 19


def test_validate_singlet_card_issue_mode():
    '''test card filtering against SINGLET deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=IssueMode.SINGLET.value,
        network="tppc",
        production=True,
        version=1,
        )

    first_issue = few_random_cards(deck, 10, 'issue', 1)  # first 10, with amount=1
    second_issue = few_random_cards(deck, 5, 'issue')  # with random amounts

    assert len(validate_card_issue_modes(deck.issue_mode, first_issue + second_issue)) == 1


def test_validate_subscription_card_issue_mode():
    '''test card filtering against SUBSCRIPTION deck'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=IssueMode.SUBSCRIPTION.value,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 10, 'issue')
    other = few_random_cards(deck, 9, 'transfer', 1)

    assert len(validate_card_issue_modes(deck.issue_mode, issues + other)) == 10


def test_validate_3combo_card_issue_mode():
    '''combo ONCE [2] and CUSTOM [1]'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=3,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 8, 'issue')
    other = few_random_cards(deck, 20, 'transfer')

    assert len(validate_card_issue_modes(deck.issue_mode, issues + other)) == 21


def test_validate_10combo_card_issue_mode():
    '''combo ONCE [2] and MONO [8]'''

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=10,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 3, 'issue', 1)
    mono_transfers = few_random_cards(deck, 2, 'transfer', 1)
    other = few_random_cards(deck, 20, 'transfer')

    assert len(validate_card_issue_modes(
               deck.issue_mode, issues + other + mono_transfers)) == 3


def test_validate_6combo_card_issue_mode():
    '''combo ONCE [2] and MULTI [4]'''

    deck = Deck(
        name="decky",
        number_of_decimals=1,
        issue_mode=6,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 3, 'issue',)
    other = few_random_cards(deck, 2, 'transfer')

    assert len(validate_card_issue_modes(
               deck.issue_mode, issues + other)) == 3


def test_validate_28combo_card_issue_mode():
    '''combo MULTI [4], MONO [8] and UNFLUSHABLE [10]'''

    mode = IssueMode.MULTI.value | IssueMode.MONO.value | IssueMode.UNFLUSHABLE.value  # 28

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=mode,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 10, 'issue', 1)
    bad_issues = few_random_cards(deck, 2, 'issue')
    other = few_random_cards(deck, 2, 'transfer', 1)

    assert len(validate_card_issue_modes(
               deck.issue_mode, issues + bad_issues + other)) == 10


def test_validate_13combo_card_issue_mode():
    '''combo CUSTOM [1], MULTI [4] and MONO [8]'''

    mode = IssueMode.CUSTOM.value | IssueMode.MULTI.value | IssueMode.MONO.value  # 13

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=mode,
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 10, 'issue', 1)
    bad_issues = few_random_cards(deck, 2, 'issue')
    other = few_random_cards(deck, 2, 'transfer', 1)

    assert len(validate_card_issue_modes(
               deck.issue_mode, issues + bad_issues + other)) == 12


@pytest.mark.parametrize("combo", list(
                         itertools.combinations(
                             [0, 1, 2, 4, 8, 16, 52, 10], 2))
                         )
def test_validate_wild_two_way_combos(combo):

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=combo[0] + combo[1],
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 5, 'issue')
    other = few_random_cards(deck, 15, 'transfer')

    assert isinstance(validate_card_issue_modes(
                      deck.issue_mode, issues + other), list)


@pytest.mark.parametrize("combo", list(
                         itertools.combinations(
                             [0, 1, 2, 4, 8, 16, 52, 10], 3))
                         )
def test_validate_wild_three_way_combos(combo):

    deck = Deck(
        name="decky",
        number_of_decimals=0,
        issue_mode=combo[0] + combo[1] + combo[2],
        network="tppc",
        production=True,
        version=1,
        )

    issues = few_random_cards(deck, 5, 'issue')
    other = few_random_cards(deck, 15, 'transfer')

    assert isinstance(validate_card_issue_modes(
                      deck.issue_mode, issues + other), list)


def test_deck_state():
    '''test DeckState calculations'''

    deck = Deck(
        name="my_test_deck",
        number_of_decimals=0,
        issue_mode=12,  # MULTI | MONO
        network="tppc",
        production=True,
        version=1,
        issuer='msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5'
        )

    receiver_roster = ['mzsMJgqVABFhrEGrqKH7qURhmxESx4K8Ti',
                       'mmsiUudS9W5xLoWeA44JmKa28cioFg7Yzx'
                       'muMpqVjUDq5voY9WnxvFb9sFvZm8wwKihu',
                       'mxrr8ALSs9fmHEszs5y1w5tRsDv9r7M2bK']
    amounts = [10, 20, 30, 40]

    card_issues = [CardTransfer(deck=deck,
                                receiver=[r],
                                amount=[a],
                                sender=deck.issuer,
                                blockseq=0,
                                txid='fe8f88c2a3a700a664f9547cb9c48466f900553d0a6bdb504ad52340ef00c9a0',
                                cardseq=amounts.index(a)
                                ) for r, a in zip(receiver_roster, amounts)]

    transfers = []  # list of card transfers

    # first member of the roster sends it's 10 cards to third member of the roster
    transfers.append(CardTransfer(deck=deck,
                                  sender=receiver_roster[0],
                                  receiver=[receiver_roster[2]],
                                  amount=[amounts[0]],
                                  blockseq=1,
                                  cardseq=0,
                                  txid='08c886a43ce9f95a5673bc95374259b0f9eca9de1e5fb9bb7aa7826834820133',
                                  type='CardTransfer'
                                  ))


    # second member of the roster burns it's 20 cards, he calls it a scam too
    transfers.append(CardTransfer(deck=deck,
                                  sender=receiver_roster[1],
                                  receiver=[deck.issuer],
                                  amount=[amounts[1]],
                                  blockseq=1,
                                  cardseq=0,
                                  txid='b27161ba476d29c2255d097aaa4e236752b9891a46d1fdb88f5225ee677b976e',
                                  type='CardBurn'
                                  ))

    # third member of the roster sends out it's cards to r[0] and r[4]
    transfers.append(CardTransfer(deck=deck,
                                  sender=receiver_roster[2],
                                  receiver=[deck.issuer],
                                  amount=[10],
                                  blockseq=1,
                                  cardseq=0,
                                  txid='ebe36158ca3f364910f8a1c0f9b1b2696bed4522f84551bdb42ffd57360ce232',
                                  type='CardTransfer'
                                  ))

    transfers.append(CardTransfer(deck=deck,
                                  sender=receiver_roster[2],
                                  receiver=[deck.issuer],
                                  amount=[20],
                                  blockseq=1,
                                  cardseq=1,
                                  txid='ebe36158ca3f364910f8a1c0f9b1b2696bed4522f84551bdb42ffd57360ce232',
                                  type='CardTransfer'
                                  ))

    state = DeckState(card_issues + transfers)

    assert state.balances['mzsMJgqVABFhrEGrqKH7qURhmxESx4K8Ti'] == 10
    assert state.balances['mt6U36PBurMsgjNVkPefYoku7uypLMRrbx'] == 0
    assert state.balances['mmsiUudS9W5xLoWeA44JmKa28cioFg7Yzx'] == 10
    assert state.balances['muobvRLAAMgEWBDNGLz1bGJ1Kj4yZUqCGj'] == 60
