from typing import Iterable, List, Optional

from pypeerassets.kutil import Kutil
from pypeerassets.protocol import Deck
from pypeerassets.provider import Provider
from pypeerassets import pavoteproto_pb2 as pavoteproto
from hashlib import sha256
from pypeerassets import transactions
from pypeerassets.pautils import read_tx_opreturn, find_tx_sender
from pypeerassets.networks import net_query

from pypeerassets.exceptions import OverSizeOPReturn


def deck_vote_tag(deck: Deck) -> str:
    '''deck vote tag address'''

    if deck.id is None:
        raise Exception("deck.id is required")

    return Kutil(network=deck.network,
                 privkey=sha256(bytearray.fromhex(deck.id) + 'vote_init'.encode()
                                ).digest()
                 ).address


class Vote:

    def __init__(self,
                 version: int,
                 description: str,
                 count_method: str,
                 start: int,
                 end: int,
                 deck: Deck,
                 choices: list=[],
                 vote_metainfo: str="",
                 id: str=None,
                 sender: str=None) -> None:
        '''initialize vote object'''

        self.version = version
        self.description = description  # short description of the vote
        self.choices = choices  # list of vote choices
        self.count_method = count_method
        self.start = start  # at which block does vote start
        self.end = end  # at which block does vote end
        self.id = id  # vote_init txid
        self.sender = sender
        self.deck = deck
        self.network = self.deck.network

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
    def metainfo_to_protobuf(self) -> str:
        '''encode vote into protobuf'''

        vote = pavoteproto.Vote()
        vote.version = self.version
        vote.description = self.description
        vote.count_method = vote.MODE.Value(self.count_method)
        vote.start = self.start
        vote.end = self.end
        vote.choices.extend(self.choices)

        if not isinstance(self.description, bytes):
            vote.description = self.description.encode()
        else:
            vote.description = self.description

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
            "count_method": self.count_method,
            "start": self.start,
            "end": self.end,
            "choices": self.choices,
            "choice_address": self.vote_choice_address
        }

        if self.description:
            r.update({'description': self.description})

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


def parse_vote_info(protobuf: bytes) -> dict:
    '''decode vote init tx op_return protobuf message and validate it.'''

    vote = pavoteproto.Vote()
    vote.ParseFromString(protobuf)

    assert vote.version > 0, {"error": "Vote info incomplete, version can't be 0."}
    assert vote.start_block < vote.end_block, {"error": "vote can't end in the past."}

    return {
        "version": vote.version,
        "description": vote.description,
        "count_mode": vote.MODE.Name(vote.count_mode),
        "choices": vote.choices,
        "start_block": vote.start_block,
        "end_block": vote.end_block,
        "vote_metainfo": vote.vote_metainfo
    }


def vote_init(vote: Vote, inputs: dict, change_address: str) -> bytes:
    '''initialize vote transaction, must be signed by the deck_issuer privkey'''

    network_params = net_query(vote.deck.network)
    deck_vote_tag_address = deck_vote_tag(vote.deck)

    tx_fee = network_params.min_tx_fee  # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": 0.01, "outputScript": transactions.monosig_script(deck_vote_tag_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(vote.to_protobuf)},
        {"redeem": float(inputs['total']) - float(tx_fee) - float(0.01),
         "outputScript": transactions.monosig_script(change_address)
         }]

    return transactions.make_raw_transaction(inputs['utxos'], outputs)


def find_vote_inits(provider: Provider, deck: Deck) -> Iterable[Vote]:
    '''find vote_inits on this deck'''

    vote_ints = provider.listtransactions(deck_vote_tag(deck))

    for txid in vote_ints:
        try:
            raw_vote = provider.getrawtransaction(txid)
            vote = parse_vote_info(read_tx_opreturn(raw_vote))
            vote["vote_id"] = txid
            vote["sender"] = find_tx_sender(provider, raw_vote)
            vote["deck"] = deck
            yield Vote(**vote)
        except AssertionError:
            pass


def vote_cast(vote: Vote, choice_index: int, inputs: dict,
              change_address: str) -> bytes:
    '''vote cast transaction'''

    network_params = net_query(vote.deck.network)
    vote_cast_addr = vote.vote_choice_address[choice_index]

    tx_fee = network_params.min_tx_fee  # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": 0.01, "outputScript": transactions.monosig_script(vote_cast_addr)},
        {"redeem": float(inputs['total']) - float(tx_fee) - float(0.01),
         "outputScript": transactions.monosig_script(change_address)
         }]

    return transactions.make_raw_transaction(inputs['utxos'], outputs)


class VoteCast:
    '''vote cast object, internal represtentation of the vote_cast transaction'''

    def __init__(self, vote: Vote, sender: str, blocknum: int,
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


def find_vote_casts(provider: Provider, vote: Vote, choice_index: int) -> Iterable[VoteCast]:
    '''find and verify vote_casts on this vote_choice_address'''

    vote_casts = provider.listtransactions(vote.vote_choice_address[choice_index])
    for tx in vote_casts:
        raw_tx = provider.getrawtransaction(tx, 1)

        sender = find_tx_sender(provider, raw_tx)
        confirmations = raw_tx["confirmations"]
        blocknum = provider.getblock(raw_tx["blockhash"])["height"]
        yield VoteCast(vote, sender, blocknum, confirmations, raw_tx["blocktime"])
