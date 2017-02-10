
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

from pypeerassets import paproto, Kutil
from pypeerassets.pautils import *

def find_all_valid_decks(provider, prod=True):
    '''
    scan the blockchain for PeerAssets decks, returns list of deck objects.
    please pass <node> - the provider
    <testnet> True/False
    <test> True/False - test or production P2TH
    '''

    decks = []
    deck_spawns = find_deck_spawns(provider) # find all deck_spawns on PAProd P2TH

    for i in deck_spawns:
        try:
            validate_deckspawn_p2th(provider, i, prod=prod, testnet=provider.is_testnet)
            if parse_deckspawn_metainfo(read_tx_opreturn(provider, i)):
                d = parse_deckspawn_metainfo(read_tx_opreturn(provider, i))
                d["asset_id"] = i
                d["time"] = provider.getrawtransaction(i, 1)["blocktime"]
                d["issuer"] = find_tx_sender(provider, i)
                decks.append(Deck(**d))

        except AssertionError:
            pass

    return decks

def find_deck(provider, key, prod=True):
    '''find specific deck by key, with key being:
    <id>, <name>, <issuer>, <issue_mode>, <number_of_decimals>
    '''

    decks = find_all_valid_decks(provider, prod=prod)
    return [d for d in decks if key in d.__dict__.values()]

class Deck:

    def __init__(self, version, name, number_of_decimals, issue_mode, asset_specific_data="",
                 issuer="", time=None, asset_id=None, network="tppc"):
        '''
        initialize deck object, load from dictionary Deck(**dict)
        or initilize with kwargs Deck(1, "deck", 3, 2)
        '''

        self.version = version # protocol version
        self.name = name # deck name
        self.issue_mode = issue_mode # deck issue mode
        assert isinstance(number_of_decimals, int), {"error": "number_of_decimals must be an integer"}
        self.number_of_decimals = number_of_decimals
        self.asset_specific_data = asset_specific_data # optional metadata for the deck
        self.asset_id = asset_id
        self.issuer = issuer
        self.issue_time = time
        self.network = network
        if self.network.startswith("t"):
            self.testnet = True
        else:
            self.testnet = False

    @property
    def p2th_address(self):
        '''P2TH address of this deck'''

        return Kutil(network=self.network, privkey=self.asset_id).address

    @property
    def p2th_wif(self):
        '''P2TH privkey in WIF format'''

        return Kutil(network=self.network, privkey=self.asset_id).wif

    @property
    def metainfo_to_protobuf(self):
        '''encode deck into protobuf'''

        deck = paproto.DeckSpawn()
        deck.version = self.version
        deck.name = self.name
        deck.number_of_decimals = self.number_of_decimals
        deck.issue_mode = deck.MODE.Value(self.issue_mode)

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

def find_all_valid_card_transfers(provider, deck):
    '''find all <deck> card transfers'''

    cards = []
    card_transfers = provider.listtransactions(deck.name)

    nderror = {"error": "Number of decimals does not match."}

    for ct in card_transfers:
        try:
            validate_card_transfer_p2th(provider, ct["txid"], deck)

            if parse_card_transfer_metainfo(read_tx_opreturn(provider, ct["txid"])):

                raw_card = parse_card_transfer_metainfo(read_tx_opreturn(provider, ct["txid"]))
                _card = {}
                _card["version"] = raw_card["version"]
                _card["number_of_decimals"] = raw_card["number_of_decimals"]
                ## check if card number of decimals matches the deck atribute
                assert _card["number_of_decimals"] == deck.number_of_decimals, nderror

                _card["deck"] = deck
                _card["txid"] = ct["txid"]
                _card["blockhash"] = ct["blockhash"]
                _card["timestamp"] = ct["time"]
                _card["sender"] = find_tx_sender(provider, ct["txid"])
                _card["asset_specific_data"] = raw_card["asset_specific_data"]

                vouts = provider.getrawtransaction(ct["txid"], 1)["vout"]

                if len(raw_card["amounts"]) > 1: ## if card states multiple outputs:
                    for am, v in zip(raw_card["amounts"], vouts[2:]):
                        c = _card.copy()
                        c["amount"] = am
                        c["receiver"] = v["scriptPubKey"]["addresses"][0]
                        cards.append(CardTransfer(**c))
                else:
                    _card["receiver"] = v["scriptPubKey"]["addresses"][0]
                    _card["amount"] = raw_card["amounts"][0]
                    cards.append(CardTransfer(**_card))

        except AssertionError:
            pass

    return cards


class CardTransfer:

    def __init__(self, version, deck, txid, sender, receiver, amount, blockhash,
                 timestamp, asset_specific_data, number_of_decimals):
        '''initialize CardTransfer object'''

        self.version = version
        self.deck_id = deck.asset_id
        self.txid = txid
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.blockhash = blockhash
        self.timestamp = timestamp
        self.asset_specific_data = asset_specific_data
        self.number_of_decimals = number_of_decimals

        if self.sender == deck.issuer:
            self.type = "CardIssue"
        elif self.receiver == deck.issuer:
            self.type = "CardBurn"
        else:
            self.type = "CardTransfer"

