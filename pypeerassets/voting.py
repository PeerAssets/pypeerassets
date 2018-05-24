import warnings
from typing import Iterable, List

from pypeerassets.kutil import Kutil
from pypeerassets.protocol import Deck
from pypeerassets.provider import Provider
from pypeerassets import pavoteproto_pb2 as pavoteproto
from hashlib import sha256
from binascii import unhexlify
from pypeerassets import transactions
from pypeerassets.pautils import read_tx_opreturn, find_tx_sender
from pypeerassets.networks import net_query


def deck_vote_tag(deck: Deck) -> str:
    '''deck vote tag address'''

    if deck.id is None:
        raise Exception("deck.id is required")

    deck_vote_tag_privkey = sha256(unhexlify(deck.id) + b"vote_init").hexdigest()
    deck_vote_tag_address = Kutil(network=deck.network, privkey=bytearray.fromhex(deck_vote_tag_privkey))
    return deck_vote_tag_address.address


class Vote:

    def __init__(self, version: int, description: str, count_mode: str,
                 start_block: int, end_block: int, deck: Deck,
                 choices: list=[], vote_metainfo: str="", vote_id: str=None, sender: str=None) -> None:
        '''initialize vote object'''

        self.version = version
        self.description = description
        self.choices = choices
        self.count_mode = count_mode
        self.start_block = start_block  # at which block does vote start
        self.end_block = end_block  # at which block does vote end
        self.vote_id = vote_id  # vote_init txid
        self.vote_metainfo = vote_metainfo  # any extra info describing the vote
        self.sender = sender
        self.deck = deck

    @property
    def to_protobuf(self) -> str:
        '''encode vote into protobuf'''

        vote = pavoteproto.Vote()
        vote.version = self.version
        vote.description = self.description
        vote.count_mode = vote.MODE.Value(self.count_mode)
        vote.start_block = self.start_block
        vote.end_block = self.end_block
        vote.choices.extend(self.choices)

        if not isinstance(self.vote_metainfo, bytes):
            vote.vote_metainfo = self.vote_metainfo.encode()
        else:
            vote.vote_metainfo = self.vote_metainfo

        proto = vote.SerializeToString()

        if len(proto) > 80:
            warnings.warn('\nMetainfo size exceeds maximum of 80 bytes allowed by OP_RETURN.')

        return proto

    @property
    def to_dict(self) -> dict:
        '''vote info as dict'''

        return {
            "version": self.version,
            "description": self.description,
            "count_mode": self.count_mode,
            "start_block": self.start_block,
            "end_block": self.end_block,
            "choices": self.choices,
            "vote_metainfo": self.vote_metainfo
        }

    @property
    def vote_choice_address(self) -> List[str]:
        '''calculate the addresses on which the vote is casted.'''

        if self.vote_id is None:
            raise Exception("vote_id is required")

        addresses = []
        vote_init_txid = unhexlify(self.vote_id)

        for choice in self.choices:
            vote_cast_privkey = sha256(vote_init_txid + bytes(
                                    list(self.choices).index(choice))
                                    ).hexdigest()
            addresses.append(Kutil(network=self.deck.network,
                                   privkey=bytearray.fromhex(vote_cast_privkey)).address)

        return addresses


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
