
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

from . import paproto

def parse_deckspawn_metainfo(protobuf):

    deck = paproto.DeckSpawn()
    deck.ParseFromString(protobuf)

    assert deck.version > 0, {"error": "Deck metainfo incomplete, version can't be 0."}
    assert deck.name is not "", {"error": "Deck metainfo incomplete, Deck must have a name."}
    assert deck.number_of_decimals > 0, {"error": '''Deck metainfo incomplete, number of decimals
                                         has to be larger than zero.'''}

    return {
        "version": deck.version,
        "name": deck.name,
        "issue_mode": deck.issue_mode,
        "number_of_decimals": deck.number_of_decimals
    }

