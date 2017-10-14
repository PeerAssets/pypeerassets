
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

import concurrent.futures
from binascii import unhexlify
from typing import Union, Generator
from .protocol import *
from .provider import *
from .pautils import (load_deck_p2th_into_local_node, 
                      find_tx_sender,
                      find_deck_spawns, tx_serialization_order,
                      read_tx_opreturn, deck_issue_mode,
                      issue_mode_to_enum, parse_deckspawn_metainfo,
                      validate_deckspawn_p2th, validate_card_transfer_p2th,
                      parse_card_transfer_metainfo, postprocess_card
                      )
from .voting import *
from .exceptions import *
from .transactions import (nulldata_output, tx_output, monosig_p2pkh,
                           make_raw_transaction)
from .constants import param_query, params
from .networks import query, networks


def find_all_valid_decks(provider, deck_version: int, prod: bool=True) -> Generator:
    '''
    Scan the blockchain for PeerAssets decks, returns list of deck objects.
    : provider - provider instance
    : version - deck protocol version (0, 1, 2, ...)
    : test True/False - test or production P2TH
    '''

    if isinstance(provider, RpcNode):
        deck_spawns = (provider.getrawtransaction(i, 1) for i in find_deck_spawns(provider))
    else:
        pa_params = param_query(provider.network)
        if prod:
            deck_spawns = (provider.getrawtransaction(i, 1) for i in
                           provider.listtransactions(pa_params.P2TH_addr))
        if not prod:
            deck_spawns = (provider.getrawtransaction(i, 1) for i in
                           provider.listtransactions(pa_params.test_P2TH_addr))

    def deck_parser(args: Union[dict, int]) -> Deck:
        '''main deck parser function'''

        raw_tx = args[0]
        deck_version = args[1]

        try:
            validate_deckspawn_p2th(provider, raw_tx, prod=prod)

            d = parse_deckspawn_metainfo(read_tx_opreturn(raw_tx), deck_version)

            if d:

                d["asset_id"] = raw_tx["txid"]
                try:
                    d["time"] = raw_tx["blocktime"]
                except KeyError:
                    d["time"] = 0
                d["issuer"] = find_tx_sender(provider, raw_tx)
                d["network"] = provider.network
                d["production"] = prod
                return Deck(**d)

        except (InvalidDeckSpawn, InvalidDeckMetainfo, InvalidDeckVersion, InvalidNulldataOutput) as err:
            pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as th:
        for result in th.map(deck_parser, ((deck, deck_version) for deck in deck_spawns)):
            if result:
                yield result


def find_deck(provider, key: str, version: int, prod=True) -> list:
    '''
    Find specific deck by key, with key being:
    <id>, <name>, <issuer>, <issue_mode>, <number_of_decimals>
    '''

    decks = find_all_valid_decks(provider, version, prod=prod)
    return [d for d in decks if key in d.__dict__.values()]


def deck_spawn(deck: Deck, inputs: dict, change_address: str) -> bytes:
    '''Creates Deck spawn raw transaction.'''

    network_params = query(deck.network)
    pa_params = param_query(deck.network)

    if deck.production:
        p2th_addr = pa_params.P2TH_addr
    else:
        p2th_addr = pa_params.test_P2TH_addr

    tx_fee = network_params.min_tx_fee # settle for min tx fee for now
    change_sum = float(inputs['total']) - float(tx_fee) - float(pa_params.P2TH_fee)

    outputs = [
        tx_output(value=pa_params.P2TH_fee, seq=0, script=monosig_p2pkh(p2th_addr)),  # p2th
        nulldata_output(value=0, seq=1, data=deck.metainfo_to_protobuf),  # op_return
        tx_output(value=change_sum, seq=2, script=monosig_p2pkh(change_address))  # change
              ]

    return make_raw_transaction(inputs['utxos'], outputs)


def deck_transfer(deck: Deck, inputs: list, change_address: str) -> bytes:
    '''
    The deck transfer transaction is a special case of the deck spawn transaction.
    Instead of registering a new asset, the deck transfer transaction transfers ownership from vin[1] to vin[0],
    meaning that both parties are required to sign the transfer transaction for it to be accepted in the blockchain.
    '''
    raise NotImplementedError


def find_card_transfers(provider, deck: Deck) -> Generator:
    '''find all <deck> card transfers'''

    if isinstance(provider, RpcNode):
        card_transfers = (provider.getrawtransaction(i["txid"], 1) for i in
                          provider.listtransactions(deck.asset_id))
    else:
        card_transfers = (provider.getrawtransaction(i, 1) for i in
                          provider.listtransactions(deck.p2th_address))

    def card_parser(args) -> list:
        '''this function wraps all the card transfer parsing'''

        provider = args[0]
        deck = args[1]
        raw_tx = args[2]

        try:
            validate_card_transfer_p2th(deck, raw_tx)  # validate P2TH first
            card_metainfo = parse_card_transfer_metainfo(read_tx_opreturn(raw_tx), deck.version)
            vouts = raw_tx["vout"]
            sender = find_tx_sender(provider, raw_tx)

            try:  # try to get block seq number
                blockseq = tx_serialization_order(provider, raw_tx["blockhash"], raw_tx["txid"])
            except KeyError:
                blockseq = None
            try:  # try to get block number of block when this tx was written
                blocknum = provider.getblock(raw_tx["blockhash"])["height"]
            except KeyError:
                blocknum = None

            cards = postprocess_card(card_metainfo, raw_tx, sender,
                                     vouts, blockseq, blocknum, deck)

        except (InvalidCardTransferP2TH, CardVersionMistmatch, CardNumberOfDecimalsMismatch) as e:
            return False

        return cards

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as th:
        for result in th.map(card_parser, ((provider, deck, i) for i in card_transfers)):
            if result:
                return (CardTransfer(**i) for i in result)


def card_issue(deck: Deck, card_transfer: CardTransfer, inputs: list, change_address: str) -> bytes:
    '''Create card issue transaction.
       :inputs - utxo [has to be owned by deck issuer]
    '''

    network_params = query(deck.network)
    pa_params = param_query(deck.network)
    tx_fee = network_params.min_tx_fee # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": pa_params.P2TH_fee, "outputScript": transactions.monosig_script(deck.p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(card_transfer.metainfo_to_protobuf)}
    ]

    for addr in card_transfer.receiver:
        outputs.append({"redeem": 0, "outputScript": transactions.monosig_script(addr)
                       })

    outputs.append(
        {"redeem": float(inputs['total']) - float(tx_fee) - float(pa_params.P2TH_fee),
         "outputScript": transactions.monosig_script(change_address)
        })

    return transactions.make_raw_transaction(deck.network, inputs['utxos'], outputs)


def card_burn(deck: Deck, card_transfer: CardTransfer, inputs: list, change_address: str) -> bytes:
    '''Create card burn transaction, cards are burned by sending the cards back to deck issuer.'''

    assert deck.issuer in card_transfer.receiver, {"error": "One of the recipients must be deck issuer."}

    network_params = query(deck.network)
    pa_params = param_query(deck.network)

    tx_fee = network_params.min_tx_fee # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": pa_params.P2TH_fee, "outputScript": transactions.monosig_script(deck.p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(card_transfer.metainfo_to_protobuf)}
    ]

    for addr in card_transfer.receiver:
        outputs.append({"redeem": 0, "outputScript": transactions.monosig_script(addr)
                       })

    outputs.append(
        {"redeem": float(inputs['total']) - float(tx_fee) - float(pa_params.P2TH_fee),
         "outputScript": transactions.monosig_script(change_address)
        })

    return transactions.make_raw_transaction(deck.network, inputs['utxos'], outputs)


def card_transfer(deck: Deck, card_transfer: CardTransfer, inputs: list, change_address: str) -> bytes:
    '''Standard peer-to-peer card transfer.'''

    network_params = query(deck.network)
    pa_params = param_query(deck.network)

    tx_fee = network_params.min_tx_fee # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": pa_params.P2TH_fee, "outputScript": transactions.monosig_script(deck.p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(card_transfer.metainfo_to_protobuf)}
    ]

    for addr in card_transfer.receiver:
        outputs.append({"redeem": 0, "outputScript": transactions.monosig_script(addr)
                       })

    outputs.append(
        {"redeem": float(inputs['total']) - float(tx_fee) - float(pa_params.P2TH_fee),
         "outputScript": transactions.monosig_script(change_address)
        })

    return transactions.make_raw_transaction(deck.network, inputs['utxos'], outputs)
