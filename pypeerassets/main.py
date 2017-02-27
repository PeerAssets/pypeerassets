
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

import concurrent.futures
from binascii import unhexlify
from .protocol import *
from .pautils import *
from . import transactions
from .constants import param_query, params
from .networks import query, networks


def find_all_valid_decks(provider, prod=True) -> list:
    '''
    Scan the blockchain for PeerAssets decks, returns list of deck objects.
    :provider - provider instance
    :test True/False - test or production P2TH
    '''

    decks = []
    deck_spawns = find_deck_spawns(provider)

    def deck_parser(i):
        try:
            validate_deckspawn_p2th(provider, i, prod=prod)
            if parse_deckspawn_metainfo(read_tx_opreturn(provider, i)):
                d = parse_deckspawn_metainfo(read_tx_opreturn(provider, i))
                d["asset_id"] = i
                try:
                    d["time"] = provider.getrawtransaction(i, 1)["blocktime"]
                except KeyError:
                    d["time"] = 0
                d["issuer"] = find_tx_sender(provider, i)
                d["network"] = provider.network
                d["production"] = prod
                decks.append(Deck(**d))

        except AssertionError:
            pass

    with concurrent.futures.ThreadPoolExecutor() as th:
        for result in th.map(deck_parser, deck_spawns):
            if result:
                decks.append(result)

    return decks

def find_deck(provider, key: str, prod=True) -> list:
    '''
    Find specific deck by key, with key being:
    <id>, <name>, <issuer>, <issue_mode>, <number_of_decimals>
    '''

    decks = find_all_valid_decks(provider, prod=prod)
    return [d for d in decks if key in d.__dict__.values()]


def deck_spawn(deck: Deck, inputs: list, change_address: str) -> bytes:
    '''Creates Deck spawn raw transaction.'''

    network_params = query(deck.network)
    pa_params = param_query(deck.network)

    if deck.production:
        p2th_addr = pa_params.P2TH_addr
    else:
        p2th_addr = pa_params.test_P2TH_addr

    tx_fee = network_params.min_tx_fee # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": pa_params.P2TH_fee, "outputScript": transactions.monosig_script(p2th_addr)},
        {"redeem": 0, "outputScript": transactions.op_return_script(deck.metainfo_to_protobuf)},
        {"redeem": float(inputs['total']) - float(tx_fee) - float(pa_params.P2TH_fee),
         "outputScript": transactions.monosig_script(change_address)
        }]

    return transactions.make_raw_transaction(deck.network, inputs['utxos'], outputs)

def deck_transfer(deck: Deck, inputs: list, change_address: str) -> bytes:
    '''
    The deck transfer transaction is a special case of the deck spawn transaction.
    Instead of registering a new asset, the deck transfer transaction transfers ownership from vin[1] to vin[0],
    meaning that both parties are required to sign the transfer transaction for it to be accepted in the blockchain.
    '''
    raise NotImplementedError

def postprocess_card(raw_card: dict, raw_tx: str, sender: str, vouts: list, deck: Deck) -> list:
    '''Postprocessing of all the relevant card transfer information and creation of CardTransfer object.'''

    nderror = {"error": "Number of decimals does not match."}

    _card = {}
    _card["version"] = raw_card["version"]
    _card["number_of_decimals"] = raw_card["number_of_decimals"]
    try: ## check if card number of decimals matches the deck atribute
        assert _card["number_of_decimals"] == deck.number_of_decimals, nderror
    except:
        return

    _card["deck"] = deck
    _card["txid"] = raw_tx["txid"]
    try:
        _card["blockhash"] = raw_tx["blockhash"]
    except KeyError:
        _card["blockhash"] = 0
    _card["timestamp"] = raw_tx["time"]
    _card["sender"] = sender
    _card["asset_specific_data"] = raw_card["asset_specific_data"]

    if len(raw_card["amount"]) > 1: ## if card states multiple outputs:
        cards = []
        for am, v in zip(raw_card["amount"], vouts[2:]):
            c = _card.copy()
            c["amount"] = [am]
            c["receiver"] = v["scriptPubKey"]["addresses"]
            cards.append(CardTransfer(**c))
        return cards
    else:
        _card["receiver"] = vouts[2]["scriptPubKey"]["addresses"]
        _card["amount"] = raw_card["amount"]
        return [CardTransfer(**_card)]

def parse_card_transfer(args):
    '''this function wraps all the card transfer parsing'''

    provider = args[0]
    deck = args[1]
    raw_tx = args[2]

    if validate_card_tx:
        metainfo = parse_card_transfer_metainfo(read_tx_opreturn(provider, raw_tx["txid"]))
        vouts = provider.getrawtransaction(raw_tx["txid"], 1)["vout"]
        sender = find_tx_sender(provider, raw_tx["txid"])
        card = postprocess_card(metainfo, raw_tx, sender, vouts, deck)

    return card

def find_card_transfers(provider, deck: Deck) -> list:
    '''find all <deck> card transfers'''

    cards = []
    card_transfers = provider.listtransactions(deck.name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as th:
        for result in th.map(parse_card_transfer, [(provider, deck, i) for i in card_transfers]):
            if result:
                cards.extend(result)

    return cards

def card_issue(deck: Deck, card_transfer: CardTransfer, inputs: list, change_address: str) -> bytes:
    '''Create card issue transaction.
       :inputs - utxo [has to be owned by deck issuer]
    '''

    issuer_error = {"error": "You must provide UTXO owned by the issuer of this deck."}

    network_params = query(deck.network)
    pa_params = param_query(deck.network)

    for utxo in inputs["utxos"]:
        assert utxo["address"] == deck.issuer, issuer_error

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

