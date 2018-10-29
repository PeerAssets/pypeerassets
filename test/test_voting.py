import pytest
from typing import Iterator

from pypeerassets.__main__ import find_all_valid_cards
from pypeerassets.protocol import DeckState
from pypeerassets import voting
from pypeerassets.protocol import (Deck, IssueMode)
from pypeerassets.transactions import Transaction
from pypeerassets.provider import Explorer
from pypeerassets.pautils import (find_tx_sender,
                                  tx_serialization_order
                                  )


deck = Deck(
    name="vote_deck",
    number_of_decimals=2,
    issue_mode=IssueMode.MULTI.value,
    network="ppc",
    production=True,
    version=1,
    id="7ee8026f5292f4953b741cc3259e1c66742a095e038642e09d6f22c2438b4467"
)


vote = voting.VoteInit(
            deck=deck,
            version=1,
            start_block=1,
            end_block=100,
            count_mode=1,  # SIMPLE vote count method
            choices=["11",
                      "3"],
            description="",
            id="0fce7f493038abb8aaa8f5b3e8130d01e5804c8dee9a19202c6cceae7c8e5e27",
            vote_metainfo="https://imgur.com/my_pic.png",
            sender=None
        )


def test_vote_tag():
    '''test deck vote tag creation'''

    assert voting.deck_vote_tag(deck).address == 'PFjDw9tJnCj3PExZPDUjY1fqFN1vtt8CUj'


def test_vote_init_object():

    vote_init = voting.VoteInit.from_json(
        {
         "deck": deck.to_json(),
         "version": 1,
         "start_block": 1,
         "end_block": 100,
         "count_mode": 1,  # SIMPLE vote count method
         "choices": ["putin"
                     "merkel",
                     "trump"],
         "description": "test vote",
         "id": "0fce7f493038abb8aaa8f5b3e8130d01e5804c8dee9a19202c6cceae7c8e5e27",
         "vote_metainfo": b"https://imgur.com/my_logo.png",
         "sender": None
        }
        )

    assert isinstance(vote_init, voting.VoteInit)

    assert isinstance(vote_init.metainfo_to_dict(), dict)

    assert isinstance(vote_init.to_json(), dict)

    assert isinstance(str(vote_init), str)

    #assert isinstance(vote_init.metainfo_to_protobuf(), bytes)


def test_parse_vote_info():
    '''test parsing vote metainfo from the OP_RETURN'''

    protobuf = b'\x08\x01\x12\x0cmy test vote\x18\xf9\x87\x16 \xe1\x8f\x16(\x012\x02no2\x03yes2\x05maybe'

    vote = voting.parse_vote_init(protobuf)

    assert isinstance(vote, dict)

    assert vote == {'choices': ['no', 'yes', 'maybe'],
                    'count_mode': 'SIMPLE',
                    'description': 'my test vote',
                    'end_block': 362465,
                    'start_block': 361465,
                    'version': 1,
                    'vote_metainfo': b''}


def test_vote_init():

    provider = Explorer(network='tppc')
    inputs = provider.select_inputs("msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5", 0.02)
    change_address = "msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5"

    my_vote = vote
    my_vote.deck.network = "tppc"

    vote_init = voting.vote_init(my_vote, inputs, change_address)

    assert isinstance(vote_init, Transaction)


def test_find_vote_inits():
    '''test finding and parsing vote inits for <deck>'''

    expected_vote_init = "6382bf31a3f8e288afd6a981e09d621d0f1bd8319cbf9657d7b332072ceffdc8"
    provider = Explorer(network='tppc')

    my_deck = deck
    my_deck.network = 'tppc'

    inits = list(voting.find_vote_inits(provider, my_deck))

    assert isinstance(inits[0], voting.VoteInit)
    assert inits[0].id == expected_vote_init


def test_vote_cast():
    '''test casting a vote'''

    provider = Explorer(network='tppc')
    inputs = provider.select_inputs("msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5", 0.02)
    change_address = "msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5"

    my_deck = deck
    my_deck.network = "tppc"

    cast = voting.vote_cast(vote=vote,
                            choice_index=0,
                            inputs=inputs,
                            change_address=change_address)

    assert isinstance(cast, Transaction)


def test_vote_object():

    provider = Explorer(network='tppc')

    raw_tx = provider.getrawtransaction('a2328f95d50261438cf4184119d84337a86cce9000e71255cbf36dbcd5c06096', 1)
    sender = find_tx_sender(provider, raw_tx)
    confirmations = raw_tx["confirmations"]
    blocknum = provider.getblock(raw_tx["blockhash"])["height"]
    blockseq = tx_serialization_order(provider,
                                      raw_tx["blockhash"],
                                      raw_tx["txid"])

    v = voting.Vote(vote_init=vote,
                    id=raw_tx['txid'],
                    sender=sender,
                    blocknum=blocknum,
                    blockseq=blockseq,
                    confirmations=confirmations,
                    timestamp=raw_tx["blocktime"]
                    )

    assert isinstance(v, voting.Vote)
    assert not v.is_valid
    assert v.blockseq == 1
    assert v.uid == "a2328f95d50261438cf4184119d84337a86cce9000e71255cbf36dbcd5c060963617591"


def test_find_casts():

    provider = Explorer(network='tppc')

    my_vote = vote
    my_vote.deck.network = 'tppc'

    casts = voting.find_vote_casts(provider, vote, 0)

    assert isinstance(casts, Iterator)
    assert isinstance(next(casts), voting.Vote)


def test_vote_state():
    '''test the VoteState object'''

    provider = Explorer(network='tppc')

    my_deck = {'asset_specific_data': b'',
               'id': 'adc6d888508ebfcad5c182df4ae94553bae6287735d76b8d64b3de8d29fc2b5b',
               'issue_mode': 4,
               'issue_time': 1527876888,
               'issuer': 'msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5',
               'p2th_wif': '',
               'name': 'peercointalk.net',
               'network': 'peercoin-testnet',
               'number_of_decimals': 3,
               'production': True,
               'tx_confirmations': 23999,
               'version': 1
               }

    vote_init = voting.VoteInit.from_json(
        {'choices': ['ne', 'ni', 'niti'],
         'count_mode': 1,
         'deck': my_deck,
         'description': 'debate.',
         'end_block': 461940,
         'id': '5020361ef0cc6f3108b9bd7f8e9b78d2b0f301aae7337e6e53c3d33a4f281e47',
         'p2th_address': 'moSZqeZrtcZJ6zNbFSJYCLCaGCwXpYdBey',
         'p2th_wif': 'cPoRWLQAKQN5hWXB5yhZP2yjK2JcTSWSfaEG6K6ZuAYrEtyEkDR8',
         'sender': None,
         'start_block': 361950,
         'version': 1,
         'vote_choice_address': ['mgHsarCrrxtcfhUPehLGqjeh6S2FHYgXT1',
                                 'mfqbSVYUKKj4Fg7efr8SfKBjvp23nBU8kt',
                                 'mwLxjNVN2MK6JtKE8mkKL8iPTz68KniDKh'],
         'vote_metainfo': ''}
    )

    state = voting.VoteState(provider, vote_init, [])

    assert isinstance(state.all_vote_casts(), dict)
    assert isinstance(state.all_valid_vote_casts(), dict)
    assert isinstance(state._sort_votes(state.all_valid_vote_casts()[2]
                                        ), list)
    assert isinstance(len(state), int)

    assert state.parsers[voting.CountMode(1).name] == voting.VoteState._simple_vote_parser


def test_vote_state_balances():

    provider = Explorer(network='tppc')

    my_deck = {'asset_specific_data': b'',
               'id': 'adc6d888508ebfcad5c182df4ae94553bae6287735d76b8d64b3de8d29fc2b5b',
               'issue_mode': 4,
               'issue_time': 1527876888,
               'issuer': 'msnHPXDWuJhRBPVNQnwXdKvEMQHLr9z1P5',
               'p2th_wif': 'mm8kkiLVQfLtLGJk52KX57SUpjXxvJ7kop',
               'name': 'peercointalk.net',
               'network': 'peercoin-testnet',
               'number_of_decimals': 3,
               'production': True,
               'tx_confirmations': 23999,
               'version': 1
               }

    vote_init = voting.VoteInit.from_json(
        {'choices': ['ne', 'ni', 'niti'],
         'count_mode': 1,
         'deck': my_deck,
         'description': 'debate.',
         'end_block': 461940,
         'id': '5020361ef0cc6f3108b9bd7f8e9b78d2b0f301aae7337e6e53c3d33a4f281e47',
         'p2th_address': 'moSZqeZrtcZJ6zNbFSJYCLCaGCwXpYdBey',
         'p2th_wif': 'cPoRWLQAKQN5hWXB5yhZP2yjK2JcTSWSfaEG6K6ZuAYrEtyEkDR8',
         'sender': None,
         'start_block': 361950,
         'version': 1,
         'vote_choice_address': ['mgHsarCrrxtcfhUPehLGqjeh6S2FHYgXT1',
                                 'mfqbSVYUKKj4Fg7efr8SfKBjvp23nBU8kt',
                                 'mwLxjNVN2MK6JtKE8mkKL8iPTz68KniDKh'],
         'vote_metainfo': ''}
    )

    all_cards = find_all_valid_cards(provider, Deck.from_json(my_deck))

    deck_state = DeckState(all_cards)

    vote_state = voting.VoteState(provider, vote_init, deck_state)

    assert isinstance(vote_state, voting.VoteState)

    # Try None CountMethod
    #vote_state.count_mode = 0

    assert isinstance(vote_state, voting.VoteState)
    assert isinstance(vote_state.calculate_state(), dict)

    #assert vote_state.calculate_state()[0] == []
    #assert vote_state.calculate_state()[1] == []
    assert len(vote_state.calculate_state()[2]) == 1
