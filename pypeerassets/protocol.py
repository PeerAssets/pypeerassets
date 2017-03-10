"""all things PeerAssets protocol."""

import warnings
from .kutil import Kutil
from . import paproto
from .pautils import amount_to_exponent, issue_mode_to_enum
from operator import itemgetter

class Deck:

    def __init__(self, name: str, number_of_decimals: int, issue_mode: str,
                 network: str, production: bool, version=1,
                 asset_specific_data="", issuer="", time=None, asset_id=None):
        '''
        Initialize deck object, load from dictionary Deck(**dict) or initilize
        with kwargs Deck("deck", 3, "ONCE")
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
        self.production = production
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
        deck.issue_mode = issue_mode_to_enum(deck, self.issue_mode)
        if not isinstance(self.asset_specific_data, bytes):
            deck.asset_specific_data = self.asset_specific_data.encode()
        else:
            deck.asset_specific_data = self.asset_specific_data

        proto = deck.SerializeToString()

        if len(proto) > 80:
            warnings.warn('\nMetainfo size exceeds maximum of 80bytes that fit into OP_RETURN.')

        return proto

    @property
    def metainfo_to_dict(self):
        '''encode deck into dictionary'''

        return {
            "version": self.version,
            "name": self.name,
            "number_of_decimals": self.number_of_decimals,
            "issue_mode": self.issue_mode
        }


class CardTransfer:

    def __init__(self, deck: Deck, receiver=[], amount=[], version=1,
                 blockhash=None, txid=None, sender=None, asset_specific_data="",
                 number_of_decimals=None, blockseq=None, blocknum=None, timestamp=None):
        '''CardTransfer object, used when parsing card_transfers from the blockchain
        or when sending out new card_transfer.
        It can be initialized by passing the **kwargs and it will do the parsing,
        or it can be initialized with passed arguments.

        * deck - instance of Deck object
        * receivers - list of receivers
        * amounts - list of amounts to be sent, must be float
        * version - protocol version, default 1
        * txid - transaction ID of CardTransfer
        * sender - transaction sender
        * blockhash - block ID where the tx was first included
        * blockseq - order in which tx was serialized into block
        * timestamp - unix timestamp of the block where it was first included
        * asset_specific_data - extra metadata
        * number_of_decimals - number of decimals for amount, inherited from Deck object'''

        assert len(amount) == len(receiver), {"error": "Amount must match receiver."}
        self.version = version
        self.deck_id = deck.asset_id
        self.txid = txid
        self.sender = sender
        self.asset_specific_data = asset_specific_data
        if not number_of_decimals:
            self.number_of_decimals = deck.number_of_decimals
        else:
            self.number_of_decimals = number_of_decimals

        self.receiver = receiver
        assert len(self.receiver) < 20, {"error": "Too many receivers."}
        self.amount = amount

        if blockhash:
            self.blockhash = blockhash
            self.blockseq = blockseq
            self.timestamp = timestamp
            self.blocknum = blocknum
        else:
            self.blockhash = 0
            self.blockseq = 0
            self.blocknum = 0
            self.timestamp = 0

        if self.sender == deck.issuer:
            self.type = "CardIssue"
        elif self.receiver[0] == deck.issuer:
            self.type = "CardBurn"
        else:
            self.type = "CardTransfer"

    @property
    def metainfo_to_protobuf(self):
        '''encode card_transfer info to protobuf'''

        card = paproto.CardTransfer()
        card.version = self.version
        card.amount.extend(self.amount)
        card.number_of_decimals = self.number_of_decimals
        if not isinstance(self.asset_specific_data, bytes):
            card.asset_specific_data = self.asset_specific_data.encode()
        else:
            card.asset_specific_data = self.asset_specific_data

        proto = card.SerializeToString()

        if len(proto) > 80:
            warnings.warn('\nMetainfo size exceeds maximum of 80bytes that fit into OP_RETURN.')

        return proto


def validate_card_issue_modes(deck: Deck, cards: list) -> list:
    """validate card transfer against deck issue mode"""

    error = {"error": "Invalid issue mode."}

    if ("ONCE", "MULTI") in deck.issue_mode:
        return error

    # first card is single and amount is 1 for SINGLET
    if deck.issue_mode == "SINGLET":
        c = next(i for i in cards if i.type == "CardIssue")
        if c.amounts[0] != 1:
            return None
        else:
            return [c]

    # only first is valid for ONCE
    if "ONCE" in deck.issue_mode:
        return [next(i for i in cards if i.type == "CardIssue")]

    if "MULTI" in deck.issue_mode:  # everything goes for multi
        return cards

    if "CUSTOM" in deck.issue_mode:  # custom issuance mode
        return cards  # what to do with this?

    else:
        return error


class DeckState:

    def __init__(self, cards: list):
        self.sort_cards(cards)
        self.total = 0
        self.burned = 0
        self.balances = {}
        self.processed_issues = {}
        self.processed_transfers = {}
        self.processed_burns = {}

        self.calc_state()
        self.checksum = not bool(self.total - sum(self.balances.values()))

    def process(self, card, ctype):

        sender = card["sender"]
        receivers = card["receiver"]
        amount = sum(card["amount"])
        
        if 'CardIssue' not in ctype:
            balance_check = sender in self.balances and self.balances[sender] >= amount

            if balance_check:
                self.balances[sender] -= amount

                if 'CardBurn' not in ctype:
                    self.to_receivers(card, receivers)

                return True

            return False

        if 'CardIssue' in ctype:
            self.to_receivers(card, receivers)
            return True

        return False

    def to_receivers(self, card, receivers):
        for i, receiver in enumerate(receivers):
            amount = card["amount"][i]
            try:
                self.balances[receiver] += amount
            except KeyError:
                self.balances[receiver] = amount


    def sort_cards(self, cards ):
        self.cards = sorted([card.__dict__ for card in cards], key=itemgetter('blocknum','blockseq'))

    def calc_state(self):

        for card in self.cards:

            txid = card["txid"]
            ctype = card["type"]
            amount = sum(card["amount"])
            if ctype == 'CardIssue' and txid not in self.processed_issues:
                validate = self.process(card, ctype)
                self.total += amount * validate # This will set amount to 0 if validate is False
                self.processed_issues[txid] = card["timestamp"]

            if ctype == 'CardTransfer' and txid not in self.processed_transfers:
                self.process(card, ctype)
                self.processed_transfers[txid] = card["timestamp"]

            if ctype == 'CardBurn' and txid not in self.processed_burns:
                validate = self.process(card, ctype)

                self.total -= amount * validate
                self.burned += amount * validate
                self.processed_burns[txid] = card["timestamp"]

