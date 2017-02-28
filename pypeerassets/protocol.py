"""all things PeerAssets protocol."""

import warnings
from .kutil import Kutil
from . import paproto
from .pautils import amount_to_exponent, exponent_to_amount

class Deck:

    def __init__(self, name: str, number_of_decimals: int, issue_mode: str, network: str, production: bool, version=1,
                 asset_specific_data="", issuer="", time=None, asset_id=None):
        '''
        Initialize deck object, load from dictionary Deck(**dict) or initilize with kwargs Deck("deck", 3, "ONCE")
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
        deck.issue_mode = deck.MODE.Value(self.issue_mode)
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

    def __init__(self, deck: Deck, receiver=[], amount=[], version=1, txid=None, sender=None, blockhash=0,
                 blockseq=None, timestamp=None, asset_specific_data="", number_of_decimals=None):
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
        self.timestamp = timestamp
        self.asset_specific_data = asset_specific_data
        self.p2th_address = deck.p2th_address
        if not number_of_decimals:
            self.number_of_decimals = deck.number_of_decimals
        else:
            self.number_of_decimals = number_of_decimals

        self.receiver = receiver
        assert len(self.receiver) < 20, {"error": "Too many receivers."}
        self.amount = []

        for i in amount:
            if not isinstance(i, float): # if not float, than it needs to be converted to float
                self.amount.append(exponent_to_amount(i, self.number_of_decimals))
            else:
                assert str(i)[::-1].find('.') <= self.number_of_decimals, {"error": "Too many decimals."}
                self.amount.append(i)

        if blockhash:
            self.blockhash = blockhash
            self.blockseq = blockseq
        else:
            self.blockhash = 0
            self.blockseq = 0

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
        card.amount.extend(
            [amount_to_exponent(i, self.number_of_decimals) for i in self.amount]
            )
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

    # first card is single and amount is 1 for SINGLET
    if deck.issue_mode == "SINGLET":
        if issues[0].amounts[0] != 1:
            return None
        else:
            return issues[0]
    # only first is valid for ONCE
    if deck.issue_mode == "ONCE":
        return list(issues)[0]
    if deck.issue_mode == "MULTI":  # everything goes for multi
        return issues
    if deck.issue_mode == "CUSTOM":  # custom issuance mode
        return  # what to do with this?

