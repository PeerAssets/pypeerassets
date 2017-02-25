
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

import warnings
import concurrent.futures
from binascii import hexlify, unhexlify
from pypeerassets import paproto, Kutil
from pypeerassets.pautils import *
from pypeerassets import transactions
from .constants import param_query, params 
from .networks import query, networks

def find_all_valid_decks(provider, prod=True) -> list:
    '''
    Scan the blockchain for PeerAssets decks, returns list of deck objects.
    :node - provider instance
    :test True/False - test or production P2TH
    '''

    decks = []
    deck_spawns = find_deck_spawns(provider) # find all deck_spawns on PAProd P2TH

    for i in deck_spawns:
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

    return decks

def find_deck(provider, key: str, prod=True) -> list:
    '''
    Find specific deck by key, with key being:
    <id>, <name>, <issuer>, <issue_mode>, <number_of_decimals>
    '''

    decks = find_all_valid_decks(provider, prod=prod)
    return [d for d in decks if key in d.__dict__.values()]

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
    ## check if card number of decimals matches the deck atribute
    assert _card["number_of_decimals"] == deck.number_of_decimals, nderror

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
            cards.extend(result)

    return cards


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

