import pytest
from pypeerassets import voting
from pypeerassets.protocol import (Deck, IssueMode)
from pypeerassets.transactions import Transaction
from pypeerassets.provider import Explorer


deck = Deck(
    name="vote_deck",
    number_of_decimals=2,
    issue_mode=IssueMode.MULTI.value,
    network="ppc",
    production=True,
    version=1,
    id="7ee8026f5292f4953b741cc3259e1c66742a095e038642e09d6f22c2438b4467"
)


def test_vote_tag():
    '''test deck vote tag creation'''

    assert voting.deck_vote_tag(deck).address == 'PFjDw9tJnCj3PExZPDUjY1fqFN1vtt8CUj'


def test_vote_object():

    vote_init = {
        "deck": deck,
        "version": 1,
        "start_block": 1,
        "end_block": 100,
        "count_mode": 1,  # SIMPLE vote count method
        "choices": [
                    "putin"
                    "merkel",
                    "trump"],
        "description": "test vote",
        "id": "0fce7f493038abb8aaa8f5b3e8130d01e5804c8dee9a19202c6cceae7c8e5e27",
        "vote_metainfo": b"https://imgur.com/my_logo.png"
    }

    vote = voting.Vote.from_json(vote_init)

    assert isinstance(vote, voting.Vote)

    assert isinstance(vote.metainfo_to_dict, dict)

    assert isinstance(vote.to_json(), dict)

    assert isinstance(str(vote), str)

    assert isinstance(vote.metainfo_to_protobuf, bytes)


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

    my_deck = deck
    my_deck.network = "tppc"

    vote = voting.Vote.from_json({
        "deck": my_deck,
        "version": 1,
        "start_block": 1,
        "end_block": 100,
        "count_mode": 1,  # SIMPLE vote count method
        "choices": [
                    "1"
                    "1",
                    "3"],
        "description": "",
        "id": "0fce7f493038abb8aaa8f5b3e8130d01e5804c8dee9a19202c6cceae7c8e5e27",
        "vote_metainfo": b"https://imgur.com/my_pic.png"
    })

    vote_init = voting.vote_init(vote, inputs, change_address)

    assert isinstance(vote_init, Transaction)
