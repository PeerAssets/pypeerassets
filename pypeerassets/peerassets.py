
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

from . import paproto

def parse_deckspawn_metainfo(protobuf):

    deck = paproto.DeckSpawn()
    deck.ParseFromString(protobuf)

    assert deck.version > 0, {"error": "Deck metainfo incomplete, version can't be 0."}
    assert deck.name is not "", {"error": "Deck metainfo incomplete, Deck must have a name."}
    assert deck.number_of_decimals > 0, {"error": '''Deck metainfo incomplete, number of decimals
                                         has to be larger than zero.'''}
    assert deck.issue_mode in (0, 1, 2, 4), {"error": "Deck metainfo incomplete, unknown issue mode."}

    return {
        "version": deck.version,
        "name": deck.name,
        "issue_mode": deck.issue_mode,
        "number_of_decimals": deck.number_of_decimals
    }

class Deck:

    def __init__(self, version, name, number_of_decimals, issue_mode):
        '''initialize deck object, load from dictionary Deck(**dict) or initilize with kwargs Deck(1, "deck", 3, 2)'''

        assert version > 0, {"error": "Version must be greater than 0."}
        self.version = version # protocol version
        assert name is not "", {"error", "Deck must have a name."}
        self.name = name # deck name
        assert number_of_decimals > 0, {"error": "Numbe of decimals must be greater than zero."}
        self.number_of_decimals = number_of_decimals # number of decimals on this deck
        assert issue_mode in (0, 1, 2, 4), {"error": "Unknown issue mode."}
        self.issue_mode = issue_mode # deck issue mode
