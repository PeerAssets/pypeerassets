"""all things PeerAssets protocol."""

import warnings
from pypeerassets.kutil import Kutil
from pypeerassets.paproto_pb2 import DeckSpawn as deckspawnproto
from pypeerassets.paproto_pb2 import CardTransfer as cardtransferproto
from pypeerassets.exceptions import RecieverAmountMismatch
from operator import itemgetter
from pypeerassets.card_parsers import parsers
from enum import Enum
from typing import List, Optional, Generator, cast, Callable


class IssueMode(Enum):

    NONE = 0x00
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L19
    # No issuance allowed.

    CUSTOM = 0x01
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L20
    # Custom issue mode, verified by client aware of this.

    ONCE = 0x02
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L21
    # A single card_issue transaction allowed.

    MULTI = 0x04
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L22
    # Multiple card_issue transactions allowed.

    MONO = 0x08
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L23
    # All card transaction amounts are equal to 1.

    UNFLUSHABLE = 0x10
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L24
    # The UNFLUSHABLE issue mode invalidates any card transfer transaction except for the card issue transaction.
    # Meaning that only the issuing entity is able to change the balance of a specific address.
    # To correctly calculate the balance of a PeerAssets addres a client should only consider the card transfer
    # transactions originating from the deck owner.

    SUBSCRIPTION = 0x34  # SUBSCRIPTION (34 = 20 | 4 | 10)
    # https://github.com/PeerAssets/rfcs/blob/master/0001-peerassets-transaction-specification.proto#L26
    # The SUBSCRIPTION issue mode marks an address holding tokens as subscribed for a limited timeframe. This timeframe is
    # defined by the balance of the account and the time at which the first cards of this token are received.
    # To check validity of a subscription one should take the timestamp of the first received cards and add the address' balance to it in hours.

    SINGLET = 0x0a  # SINGLET is a combination of ONCE and MONO (2 | 8)
    #  Singlet deck, one MONO card issunce allowed


class Deck:

    def __init__(self, name: str, number_of_decimals: int, issue_mode: int,
                 network: str, production: bool, version: int,
                 asset_specific_data: bytes=None, issuer: str="", time: int=None,
                 id: str=None, tx_confirmations: int=None) -> None:
        '''
        Initialize deck object, load from dictionary Deck(**dict) or initilize
        with kwargs Deck("deck", 3, "ONCE")
        '''

        self.version = version  # protocol version
        self.name = name  # deck name
        self.issue_mode = issue_mode  # deck issue mode
        self.number_of_decimals = number_of_decimals
        self.asset_specific_data = asset_specific_data  # optional metadata for the deck
        self.id = id
        self.issuer = issuer
        self.issue_time = time
        self.confirms = tx_confirmations
        self.network = network
        self.production = production
        if self.network.startswith("t") or 'testnet' in self.network:
            self.testnet = True
        else:
            self.testnet = False

    @property
    def p2th_address(self) -> Optional[str]:
        '''P2TH address of this deck'''

        if self.id:
            return Kutil(network=self.network,
                         privkey=bytearray.fromhex(self.id)).address
        else:
            return None

    @property
    def p2th_wif(self) -> Optional[str]:
        '''P2TH privkey in WIF format'''

        if self.id:
            return Kutil(network=self.network,
                         privkey=bytearray.fromhex(self.id)).wif
        else:
            return None

    @property
    def metainfo_to_protobuf(self) -> bytes:
        '''encode deck into protobuf'''

        deck = deckspawnproto()
        deck.version = self.version
        deck.name = self.name
        deck.number_of_decimals = self.number_of_decimals
        deck.issue_mode = self.issue_mode
        if self.asset_specific_data:
            if not isinstance(self.asset_specific_data, bytes):
                deck.asset_specific_data = self.asset_specific_data.encode()
            else:
                deck.asset_specific_data = self.asset_specific_data

        proto = deck.SerializeToString()

        if len(proto) > 80:
            warnings.warn('\nMetainfo size exceeds maximum of 80bytes that fit into OP_RETURN.')

        return proto

    @property
    def metainfo_to_dict(self) -> dict:
        '''encode deck into dictionary'''

        r = {
            "version": self.version,
            "name": self.name,
            "number_of_decimals": self.number_of_decimals,
            "issue_mode": self.issue_mode
        }

        if self.asset_specific_data:
            r.update({'asset_specific_data': self.asset_specific_data})

        return r

    def __str__(self) -> str:

        r = []
        for key in self.__dict__:
            r.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(r)


class CardTransfer:

    def __init__(self, deck: Deck, receiver: list=[], amount: List[int]=[],
                 version: int=1, blockhash: str=None, txid: str=None,
                 sender: str=None, asset_specific_data: bytes=None,
                 number_of_decimals: int=None, blockseq: int=None,
                 cardseq: int=None, blocknum: int=None,
                 timestamp: int=None, tx_confirmations: int=None,
                 type: str=None) -> None:

        '''CardTransfer object, used when parsing card_transfers from the blockchain
        or when sending out new card_transfer.
        It can be initialized by passing the **kwargs and it will do the parsing,
        or it can be initialized with passed arguments.

        * deck - instance of Deck object
        * receiver - list of receivers
        * amount - list of amounts to be sent, must be integer
        * version - protocol version, default 1
        * txid - transaction ID of CardTransfer
        * sender - transaction sender
        * blockhash - block ID where the tx was first included
        * blockseq - order in which tx was serialized into block
        * timestamp - unix timestamp of the block where it was first included
        * tx_confirmations - number of confirmations of the transaction
        * asset_specific_data - extra metadata
        * number_of_decimals - number of decimals for amount, inherited from Deck object
        : type: card type [CardIssue, CardTransfer, CardBurn]'''

        if not len(amount) == len(receiver):
            raise RecieverAmountMismatch({"error": "carn mmount must match card receiver."})

        self.version = version
        self.deck_id = deck.id
        self.deck_p2th = deck.p2th_address
        self.txid = txid
        self.sender = sender
        self.asset_specific_data = asset_specific_data
        if not number_of_decimals:
            self.number_of_decimals = deck.number_of_decimals
        else:
            self.number_of_decimals = number_of_decimals

        self.receiver = receiver
        self.amount = amount

        if blockhash:
            self.blockhash = blockhash
            self.blockseq = blockseq
            self.timestamp = timestamp
            self.blocknum = blocknum
            self.cardseq = cardseq
            self.confirms = tx_confirmations
        else:
            self.blockhash = ""
            self.blockseq = 0
            self.blocknum = 0
            self.timestamp = 0
            self.cardseq = 0
            self.confirms = 0

        if type:
            self.type = type

        if self.sender == deck.issuer:
            self.type = "CardIssue"
        elif self.receiver[0] == deck.issuer:
            self.type = "CardBurn"
        else:
            self.type = "CardTransfer"

    @property
    def metainfo_to_protobuf(self) -> bytes:
        '''encode card_transfer info to protobuf'''

        card = cardtransferproto()
        card.version = self.version
        card.amount.extend(self.amount)
        card.number_of_decimals = self.number_of_decimals
        if self.asset_specific_data:
            if not isinstance(self.asset_specific_data, bytes):
                card.asset_specific_data = self.asset_specific_data.encode()
            else:
                card.asset_specific_data = self.asset_specific_data

        proto = card.SerializeToString()

        if len(proto) > 80:
            warnings.warn('\nMetainfo size exceeds maximum of 80bytes that fit into OP_RETURN.')

        return proto

    @property
    def metainfo_to_dict(self) -> dict:
        '''encode card into dictionary'''

        r = {
            "version": self.version,
            "amount": self.amount,
            "number_of_decimals": self.number_of_decimals
        }

        if self.asset_specific_data:
            r.update({'asset_specific_data': self.asset_specific_data})

        return r

    def __str__(self) -> str:

        r = []
        for key in self.__dict__:
            r.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(r)


def validate_card_issue_modes(issue_mode: int, cards: list) -> list:
    """validate cards against deck_issue modes"""

    supported_mask = 63  # sum of all issue_mode values

    if not bool(issue_mode & supported_mask):
        return []  # return empty list

    for i in [1 << x for x in range(len(IssueMode))]:
        if bool(i & issue_mode):

            try:
                parser_fn = cast(
                    Callable[[list], Optional[list]],
                    parsers[IssueMode(i).name]
                )
            except ValueError:
                continue

            parsed_cards = parser_fn(cards)
            if not parsed_cards:
                return []
            cards = parsed_cards

    return cards


class DeckState:

    def __init__(self, cards: Generator) -> None:

        self.cards = cards
        self.total = 0
        self.burned = 0
        self.balances = cast(dict, {})
        self.processed_issues = set()
        self.processed_transfers = set()
        self.processed_burns = set()

        self.calc_state()
        self.checksum = not bool(self.total - sum(self.balances.values()))

    def _process(self, card: dict, ctype: str) -> bool:

        sender = card["sender"]
        receiver = card["receiver"][0]
        amount = card["amount"][0]

        if ctype != 'CardIssue':
            balance_check = sender in self.balances and self.balances[sender] >= amount

            if balance_check:
                self.balances[sender] -= amount

                if 'CardBurn' not in ctype:
                    self._append_balance(amount, receiver)

                return True

            return False

        if 'CardIssue' in ctype:
            self._append_balance(amount, receiver)
            return True

        return False

    def _append_balance(self, amount: int, receiver: str) -> None:

            try:
                self.balances[receiver] += amount
            except KeyError:
                self.balances[receiver] = amount

    def _sort_cards(self, cards: Generator) -> list:
        '''sort cards by blocknum and blockseq'''

        return sorted([card.__dict__ for card in cards],
                            key=itemgetter('blocknum', 'blockseq', 'cardseq'))

    def calc_state(self) -> None:

        for card in self._sort_cards(self.cards):

            # txid + blockseq + cardseq, as unique ID
            cid = str(card["txid"] + str(card["blockseq"]) + str(card["cardseq"]))
            ctype = card["type"]
            amount = card["amount"][0]

            if ctype == 'CardIssue' and cid not in self.processed_issues:
                validate = self._process(card, ctype)
                self.total += amount * validate  # This will set amount to 0 if validate is False
                self.processed_issues |= {cid}

            if ctype == 'CardTransfer' and cid not in self.processed_transfers:
                self._process(card, ctype)
                self.processed_transfers |= {cid}

            if ctype == 'CardBurn' and cid not in self.processed_burns:
                validate = self._process(card, ctype)

                self.total -= amount * validate
                self.burned += amount * validate
                self.processed_burns |= {cid}
