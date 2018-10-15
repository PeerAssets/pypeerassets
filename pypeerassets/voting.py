from typing import Iterable, List, Optional
from enum import Enum
from decimal import Decimal

from pypeerassets.kutil import Kutil
from pypeerassets.protocol import Deck
from pypeerassets.provider import Provider
from pypeerassets.pavoteproto_pb2 import Vote as pavoteproto
from hashlib import sha256

from pypeerassets.pautils import read_tx_opreturn, find_tx_sender
from pypeerassets.networks import net_query

from pypeerassets.exceptions import (OverSizeOPReturn,
                                     InvalidVoteVersion,
                                     InvalidVoteEndBlock
                                     )

from pypeerassets.transactions import (tx_output,
                                       p2pkh_script,
                                       nulldata_script,
                                       Transaction,
                                       make_raw_transaction,
                                       Locktime
                                       )


class CountMethod(Enum):

    NONE = 0x00
    # Nothing, just placeholder.

    SIMPLE = 0x01
    # https://github.com/PeerAssets/peerassets-rfcs/blob/master/0005-on-chain-voting-protocol-proposal.md#simple-vote-counting
    """
    Simplest form of vote counting is counting one vote per transaction, with filtering of double votes and invalid votes.
    Filtering is done by using "first come, first served" rule, where only the first vote is registered and subsequent ones are dismissed as invalid.
    The only requisite of valid vote with this schema is positive card balance.
    However this schema is easily gamed by buying cards just before casting a vote and selling them after the vote has been casted,
    so two more complex voting schemes are proposed bellow.
    """

    WEIGHT_CARD_BALANCE = 0x03
    # https://github.com/PeerAssets/peerassets-rfcs/blob/master/0005-on-chain-voting-protocol-proposal.md#weighting-votes-with-pa-card-balance
    """
    This schema allows weighting the vote with PeerAssets card balance.
    This allows equating casted vote with stake in the PeerAssets deck.
    Simplest form of card balance weighted voting is using card balance when summing up votes.
    Same rule of "first come, first served" is applied to prevent double voting.
    """

    WEIGHT_CARD_DAYS = 0x07
    # https://github.com/PeerAssets/peerassets-rfcs/blob/master/0005-on-chain-voting-protocol-proposal.md#weighting-vote-with-pa-card-days
    """
    Votes are counted as card days, card balance is multiplied with age of UTXO which was used to deliver the cards.
    This schema prevents "last minute" vote manipulations by giving more weight to older card holders.
    """


def deck_vote_tag(deck: Deck) -> Kutil:
    '''deck vote tag address'''

    if deck.id is None:
        raise Exception("deck.id is required")

    return Kutil(network=deck.network,
                 privkey=sha256(bytearray.fromhex(deck.id) + 'vote_init'.encode()
                                ).digest()
                 )


class VoteInit:

    def __init__(self,
                 version: int,
                 description: str,
                 count_mode: int,
                 start_block: int,
                 end_block: int,
                 deck: Deck,
                 choices: List[str]=[],
                 vote_metainfo: str="",
                 id: str=None,
                 sender: str=None) -> None:
        '''initialize vote object'''

        self.version = version
        self.description = description  # short description of the vote
        self.choices = choices  # list of vote choices
        self.count_mode = count_mode
        self.start_block = start_block  # at which block does vote start
        self.end_block = end_block  # at which block does vote end
        self.id = id  # vote_init txid
        self.vote_metainfo = vote_metainfo
        self.sender = sender
        self.deck = deck
        self.network = self.deck.network

    @property
    def p2th_address(self) -> Optional[str]:
        '''P2TH address for the deck vote'''

        if self.deck.id:
            return deck_vote_tag(self.deck).address
        else:
            return None

    @property
    def p2th_wif(self) -> Optional[str]:
        '''P2TH privkey in WIF format'''

        if self.id:
            return deck_vote_tag(self.deck).wif
        else:
            return None

    @property
    def metainfo_to_protobuf(self) -> bytes:
        '''encode vote into protobuf'''

        vote = pavoteproto()
        vote.version = self.version
        vote.description = self.description
        vote.count_mode = self.count_mode
        vote.start_block = self.start_block
        vote.end_block = self.end_block
        vote.choices.extend(self.choices)

        if not isinstance(self.vote_metainfo, bytes):
            vote.vote_metainfo = self.vote_metainfo.encode()
        else:
            vote.vote_metainfo = self.vote_metainfo

        if vote.ByteSize() > net_query(self.network).op_return_max_bytes:
            raise OverSizeOPReturn('''
                        Metainfo size exceeds maximum of {max} bytes supported by this network.'''
                                   .format(max=net_query(self.network)
                                           .op_return_max_bytes))
        return vote.SerializeToString()

    @property
    def metainfo_to_dict(self) -> dict:
        '''vote info as dict'''

        r = {
            "version": self.version,
            "count_mode": self.count_mode,
            "start_block": self.start_block,
            "end_block": self.end_block,
            "choices": self.choices,
            "choice_address": self.vote_choice_address,
            "description": self.description
        }

        if self.vote_metainfo:
            r.update({'vote_metainfo': self.vote_metainfo})

        return r

    @property
    def vote_choice_address(self) -> List[str]:
        '''calculate the addresses on which the vote is casted.'''

        if self.id is None:
            raise Exception("vote id is required")

        addresses = []

        for choice in self.choices:

            addresses.append(
                Kutil(network=self.deck.network,
                      privkey=sha256(bytearray.fromhex(self.id) +
                                     bytearray(self.choices.index(choice))
                                     ).digest()
                      ).address
            )

        return addresses

    def to_json(self) -> dict:
        '''export the Vote object to json-ready format'''

        d = self.__dict__
        d['p2th_address'] = self.p2th_address
        d['p2th_wif'] = self.p2th_wif
        d['vote_choice_address'] = self.vote_choice_address
        return d

    @classmethod
    def from_json(cls, json: dict):
        '''load the Deck object from json'''

        return cls(**json)

    def __str__(self) -> str:

        r = []
        for key in self.__dict__:
            r.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(r)


def parse_vote_init(protobuf: bytes) -> dict:
    '''decode vote init tx op_return protobuf message and validate it.'''

    vote = pavoteproto()
    vote.ParseFromString(protobuf)

    if not vote.version > 0:
        raise InvalidVoteVersion(
            {"error": "Vote info incomplete, version can't be 0."}
        )

    if vote.start_block > vote.end_block:
        raise InvalidVoteEndBlock(
            {"error": "vote can't end in the past."}
        )

    return {
        "version": vote.version,
        "description": vote.description,
        "count_mode": vote.MODE.Name(vote.count_mode),
        "choices": vote.choices,
        "start_block": vote.start_block,
        "end_block": vote.end_block,
        "vote_metainfo": vote.vote_metainfo
    }


def vote_init(vote: VoteInit, inputs: dict, change_address: str,
              locktime: int=0) -> Transaction:
    '''initialize vote transaction, must be signed by the deck_issuer privkey'''

    network_params = net_query(vote.deck.network)
    p2th = vote.p2th_address

    #  first round of txn making is done by presuming minimal fee
    change_sum = Decimal(inputs['total'] - network_params.min_tx_fee - Decimal(0.01))
    # this final 0.01 deduced from the fee is to accomodate for the vote_init p2th fee

    txouts = [
        tx_output(network=vote.deck.network, value=Decimal(0.01),
                  n=0, script=p2pkh_script(address=p2th,
                                           network=vote.deck.network)),  # p2th

        tx_output(network=vote.deck.network, value=Decimal(0),
                  n=1, script=nulldata_script(vote.metainfo_to_protobuf)),  # op_return

        tx_output(network=vote.deck.network, value=change_sum,
                  n=2, script=p2pkh_script(address=change_address,
                                           network=vote.deck.network))  # change
              ]

    unsigned_tx = make_raw_transaction(network=vote.deck.network,
                                       inputs=inputs['utxos'],
                                       outputs=txouts,
                                       locktime=Locktime(locktime)
                                       )
    return unsigned_tx


def find_vote_inits(provider: Provider, deck: Deck) -> Iterable[VoteInit]:
    '''find vote_inits on this deck'''

    vote_ints = provider.listtransactions(deck_vote_tag(deck).address)

    for txid in vote_ints:
        try:
            raw_vote = provider.getrawtransaction(txid, 1)
            vote = parse_vote_init(read_tx_opreturn(raw_vote["vout"][1])
                                   )
            vote["id"] = txid
            vote["sender"] = find_tx_sender(provider, raw_vote)
            vote["deck"] = deck

            yield VoteInit.from_json(vote)

        except (InvalidVoteVersion,
                InvalidVoteEndBlock) as e:
            pass


def vote_cast(vote: VoteInit, choice_index: int, inputs: dict,
              change_address: str,
              locktime: int=0) -> Transaction:
    '''vote cast transaction'''

    network_params = net_query(vote.deck.network)
    p2th = vote.vote_choice_address[choice_index]

    #  first round of txn making is done by presuming minimal fee
    change_sum = Decimal(inputs['total'] - network_params.min_tx_fee - Decimal(0.01))

    txouts = [
        tx_output(network=vote.deck.network, value=Decimal(0.01),
                  n=0, script=p2pkh_script(address=p2th,
                                           network=vote.deck.network)),  # p2th

        tx_output(network=vote.deck.network, value=change_sum,
                  n=1, script=p2pkh_script(address=change_address,
                                           network=vote.deck.network))  # change
              ]

    unsigned_tx = make_raw_transaction(network=vote.deck.network,
                                       inputs=inputs['utxos'],
                                       outputs=txouts,
                                       locktime=Locktime(locktime)
                                       )
    return unsigned_tx


class VoteCast:
    '''vote cast object, internal represtentation of the vote_cast transaction'''

    def __init__(self, vote: VoteInit, sender: str, blocknum: int,
                 confirmations: int, timestamp: int) -> None:
        self.vote = vote
        self.sender = sender
        self.blocknum = blocknum
        self.confirmations = confirmations
        self.timestamp = timestamp

    @property
    def is_valid(self) -> bool:
        '''check if VoteCast is valid'''

        if not (self.blocknum >= self.vote.start_block and
                self.blocknum <= self.vote.end_block):
            return False

        if not self.confirmations >= 6:
            return False

        return True


def find_vote_casts(provider: Provider, vote: VoteInit, choice_index: int) -> Iterable[VoteCast]:
    '''find and verify vote_casts on this vote_choice_address'''

    vote_casts = provider.listtransactions(vote.vote_choice_address[choice_index])
    for tx in vote_casts:
        raw_tx = provider.getrawtransaction(tx, 1)

        sender = find_tx_sender(provider, raw_tx)
        confirmations = raw_tx["confirmations"]
        blocknum = provider.getblock(raw_tx["blockhash"])["height"]
        yield VoteCast(vote, sender, blocknum, confirmations, raw_tx["blocktime"])
