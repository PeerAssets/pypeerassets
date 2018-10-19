"""all things PeerAssets protocol."""

from enum import Enum
from operator import itemgetter
from typing import List, Optional, Generator, cast, Callable

from pypeerassets.kutil import Kutil
from pypeerassets.paproto_pb2 import DeckSpawn as deckspawnproto
from pypeerassets.paproto_pb2 import CardTransfer as cardtransferproto
from pypeerassets.exceptions import (
    InvalidCardIssue,
    OverSizeOPReturn,
    RecieverAmountMismatch,
)
from pypeerassets.card_parsers import parsers
from pypeerassets.networks import net_query


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

    def __init__(self, name: str,
                 number_of_decimals: int,
                 issue_mode: int,
                 network: str,
                 production: bool,
                 version: int,
                 asset_specific_data: bytes=None,
                 issuer: str="",
                 issue_time: int=None,
                 id: str=None,
                 tx_confirmations: int=None) -> None:
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
        self.issue_time = issue_time
        self.tx_confirmations = tx_confirmations
        self.network = network
        self.production = production

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

        if deck.ByteSize() > net_query(self.network).op_return_max_bytes:
            raise OverSizeOPReturn('''
                        Metainfo size exceeds maximum of {max} bytes supported by this network.'''
                                   .format(max=net_query(self.network)
                                           .op_return_max_bytes))

        return deck.SerializeToString()

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

    def to_json(self) -> dict:
        '''export the Deck object to json-ready format'''

        d = self.__dict__
        d['p2th_wif'] = self.p2th_wif
        return d

    @classmethod
    def from_json(cls, json: dict):
        '''load the Deck object from json'''

        return cls(**{
            "version": json["version"],
            "name": json["name"],
            "issue_mode": json["issue_mode"],
            "number_of_decimals": json["number_of_decimals"],
            "asset_specific_data": json["asset_specific_data"],
            "id": json["id"],
            "issuer": json["issuer"],
            "issue_time": json["issue_time"],
            "tx_confirmations": json["tx_confirmations"],
            "network": json["network"],
            "production": json["production"]
        })

    def __str__(self) -> str:

        r = []
        for key in self.__dict__:
            r.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(r)


class CardBundle:

    '''On the low level, cards come in bundles.
    A single transaction can contain dozens of cards.
    CardBundle is a object which is pre-coursor to CardTransfer'''

    def __init__(self,
                 deck: Deck,
                 sender: str,
                 txid: str,
                 blockhash: str,
                 blocknum: int,
                 blockseq: int,
                 timestamp: int,
                 tx_confirmations: int,
                 vouts: list=[],
                 ) -> None:

        self.deck = deck
        self.txid = txid
        self.sender = sender
        self.vouts = vouts

        if blockhash:
            self.blockhash = blockhash
            self.blockseq = blockseq
            self.timestamp = timestamp
            self.blocknum = blocknum
            self.tx_confirmations = tx_confirmations
        else:
            self.blockhash = ""
            self.blockseq = 0
            self.blocknum = 0
            self.timestamp = 0
            self.tx_confirmations = 0

    def to_json(self) -> dict:
        '''export the CardBundle object to json-ready format'''

        return self.__dict__


class CardTransfer:

    def __init__(self, deck: Deck, 
                 receiver: list=[],
                 amount: List[int]=[],
                 version: int=1,
                 blockhash: str=None,
                 txid: str=None,
                 sender: str=None,
                 asset_specific_data: bytes=None,
                 number_of_decimals: int=None,
                 blockseq: int=None,
                 cardseq: int=None,
                 blocknum: int=None,
                 timestamp: int=None,
                 tx_confirmations: int=None,
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

        if not len(receiver) == len(amount):
            raise RecieverAmountMismatch

        self.version = version
        self.network = deck.network
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
            self.tx_confirmations = tx_confirmations
        else:
            self.blockhash = ""
            self.blockseq = 0
            self.blocknum = 0
            self.timestamp = 0
            self.cardseq = 0
            self.tx_confirmations = 0

        if self.sender == deck.issuer:
            # if deck issuer is issuing cards to the deck issuing address,
            # card is burn and issue at the same time - which is invalid!
            if deck.issuer in self.receiver:
                raise InvalidCardIssue
            else:
                # card was sent from deck issuer to any random address,
                # card type is CardIssue
                self.type = "CardIssue"

        # card was sent back to issuing address
        # card type is CardBurn
        elif self.receiver[0] == deck.issuer and not self.sender == deck.issuer:
            self.type = "CardBurn"

        # issuer is anyone else,
        # card type is CardTransfer
        else:
            self.type = "CardTransfer"

        if type:
            self.type = type

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

        if card.ByteSize() > net_query(self.network).op_return_max_bytes:
            raise OverSizeOPReturn('''
                        Metainfo size exceeds maximum of {max} bytes supported by this network.'''
                                   .format(max=net_query(self.network)
                                           .op_return_max_bytes))

        return card.SerializeToString()

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

    def to_json(self) -> dict:
        '''export the CardTransfer object to json-ready format'''

        return self.__dict__

    @classmethod
    def from_json(cls, json: dict):
        '''load the Deck object from json'''

        return cls(**json)

    def __str__(self) -> str:

        r = []
        for key in self.__dict__:
            r.append("{key}='{value}'".format(key=key, value=self.to_json()[key]))

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
