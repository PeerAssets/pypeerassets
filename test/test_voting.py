import pytest
from pypeerassets import voting
from pypeerassets.protocol import (Deck, IssueMode)


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

    assert voting.deck_vote_tag(deck) == 'PFjDw9tJnCj3PExZPDUjY1fqFN1vtt8CUj'


def test_vote_object():

    vote_init = {
        "deck": deck,
        "version": 1,
        "start": 1,
        "end": 100,
        "count_method": "weight_card_days",
        "choices": [
                    "putin"
                    "merkel",
                    "trump"],
        "description": "test vote",
        "id": "0fce7f493038abb8aaa8f5b3e8130d01e5804c8dee9a19202c6cceae7c8e5e27"
    }

    vote = voting.Vote(**vote_init)

    assert isinstance(vote, voting.Vote)

    assert isinstance(vote.metainfo_to_dict, dict)

    assert isinstance(vote.to_json(), dict)

    assert isinstance(str(vote), str)

    assert isinstance(vote.metainfo_to_protobuf, bytes)
