
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

from pypeerassets import paproto

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

    @property
    def to_protobuf(self):
        '''encode deck into protobuf'''

        deck = paproto.DeckSpawn()
        deck.version = self.version
        deck.name = self.name
        deck.number_of_decimals = self.number_of_decimals
        deck.issue_mode = self.issue_mode

        return deck.SerializeToString()

    @property
    def to_dict(self):
        '''encode deck into dictionary'''

        return {
            "version": self.version,
            "name": self.name,
            "number_of_decimals": self.number_of_decimals,
            "issue_mode": self.issue_mode
        }

