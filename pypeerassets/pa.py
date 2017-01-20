
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

from pypeerassets import paproto, pautils, Kutil, RpcNode

def find_all_valid_decks(node, testnet=True, test=False):
    '''
    scan the blockchain for PeerAssets decks, returns list of deck objects.
    please pass <node> - the provider
    <testnet> True/False
    <test> True/False - test or production P2TH
    '''

    decks = []
    deck_spawns = pautils.find_deck_spawns(node) # find all deck_spawns on PAProd P2TH

    for i in deck_spawns:
        try:
            pautils.validate_deckspawn_p2th(node, i, testnet=testnet)
            if pautils.parse_deckspawn_metainfo(pautils.read_tx_opreturn(node, i)):
                d = pautils.parse_deckspawn_metainfo(pautils.read_tx_opreturn(node, i))
                d["asset_id"] = i
                decks.append(Deck(**d))

        except AssertionError:
            pass

    return decks

class Deck:

    def __init__(self, version, name, number_of_decimals, issue_mode, asset_specific_data="",
                 asset_id=None, network="tppc"):
        '''
        initialize deck object, load from dictionary Deck(**dict)
        or initilize with kwargs Deck(1, "deck", 3, 2)
        '''

        self.version = version # protocol version
        self.name = name # deck name
        self.issue_mode = issue_mode # deck issue mode
        self.number_of_decimals = number_of_decimals
        self.asset_specific_data = asset_specific_data # optional metadata for the deck
        self.asset_id = asset_id
        self.network = network
        if self.network.startswith("t"):
            self.testnet = True
        else:
            self.testnet = False

    @property
    def p2th_address(self):
        '''P2TH address of this deck'''

        return Kutil(network=self.network, seed=self.asset_id).address

    @property
    def p2th_wif(self):
        '''P2TH privkey in WIF format'''

        return Kutil(network=self.network, seed=self.asset_id).wif

    @property
    def metainfo_to_protobuf(self):
        '''encode deck into protobuf'''

        deck = paproto.DeckSpawn()
        deck.version = self.version
        deck.name = self.name
        deck.number_of_decimals = self.number_of_decimals
        deck.issue_mode = self.issue_mode

        return deck.SerializeToString()

    @property
    def metainfo_to_dict(self):
        '''encode deck into dictionary'''

        return {
            "version": self.version,
            "name": self.name,
            "number_of_decimals": self.number_of_decimals,
            "issue_mode": self.issue_mode
        }
