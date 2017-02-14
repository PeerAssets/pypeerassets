
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

import warnings
from binascii import hexlify, unhexlify
from pypeerassets import paproto, Kutil
from pypeerassets.pautils import *
from pypeerassets import constants, transactions
from .networks import query, networks

def find_all_valid_decks(provider, prod=True):
    '''
    scan the blockchain for PeerAssets decks, returns list of deck objects.
    please pass <node> - the provider
    <testnet> True/False
    <test> True/False - test or production P2TH
    '''

    decks = []
    deck_spawns = find_deck_spawns(provider) # find all deck_spawns on PAProd P2TH

    for i in deck_spawns:
        try:
            validate_deckspawn_p2th(provider, i, prod=prod, testnet=provider.is_testnet)
            if parse_deckspawn_metainfo(read_tx_opreturn(provider, i)):
                d = parse_deckspawn_metainfo(read_tx_opreturn(provider, i))
                d["asset_id"] = i
                d["time"] = provider.getrawtransaction(i, 1)["blocktime"]
                d["issuer"] = find_tx_sender(provider, i)
                decks.append(Deck(**d))

        except AssertionError:
            pass

    return decks

def find_deck(provider, key, prod=True):
    '''find specific deck by key, with key being:
    <id>, <name>, <issuer>, <issue_mode>, <number_of_decimals>
    '''

    decks = find_all_valid_decks(provider, prod=prod)
    return [d for d in decks if key in d.__dict__.values()]

class Deck:

    def __init__(self, name, number_of_decimals, issue_mode, version=1, asset_specific_data="",
                 issuer="", time=None, asset_id=None, network="tppc"):
        '''
        initialize deck object, load from dictionary Deck(**dict)
        or initilize with kwargs Deck(1, "deck", 3, 2)
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
        deck.asset_specific_data = self.asset_specific_data.encode()

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

def deck_spawn(deck, network, inputs, change_address, prod=True):
    '''spawn new deck, returns raw unsigned transaction'''

    network_params = query(network)

    if network.startswith("t"):
        p2th_fee = constants.testnet_p2th_fee
        if prod:
            p2th_address = constants.testnet_PAPROD_addr
        else:
            p2th_address = constants.testnet_PATEST_addr

    else:
        p2th_fee = constants.mainnet_p2th_fee
        if prod:
            p2th_address = constants.mainnet_PAPROD_addr
        else:
            p2th_address = constants.mainnet_PATEST_addr

    tx_fee = network_params.min_tx_fee # settle for min tx fee for now

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": p2th_fee, "outputScript": transactions.monosig_script(p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(deck.metainfo_to_protobuf)},
        {"redeem": float(inputs['total']) - float(tx_fee) - float(p2th_fee), "outputScript": transactions.monosig_script(change_address)
        }]

    return transactions.make_raw_transaction(network, inputs['utxos'], outputs)

def deck_transfer(deck, network, inputs, change_address, prod=True):
    '''
    The deck transfer transaction is a special case of the deck spawn transaction.
    Instead of registering a new asset, the deck transfer transaction transfers ownership from vin[1] to vin[0],
    meaning that both parties are required to sign the transfer transaction for it to be accepted in the blockchain.
    '''
    raise NotImplementedError

def find_all_card_transfers(provider, deck):
    '''find all <deck> card transfers'''

    cards = []
    card_transfers = provider.listtransactions(deck.name)

    nderror = {"error": "Number of decimals does not match."}

    for ct in card_transfers:
        try:
            validate_card_transfer_p2th(provider, ct["txid"], deck)

            if parse_card_transfer_metainfo(read_tx_opreturn(provider, ct["txid"])):

                raw_card = parse_card_transfer_metainfo(read_tx_opreturn(provider, ct["txid"]))
                _card = {}
                _card["version"] = raw_card["version"]
                _card["number_of_decimals"] = raw_card["number_of_decimals"]
                ## check if card number of decimals matches the deck atribute
                assert _card["number_of_decimals"] == deck.number_of_decimals, nderror

                _card["deck"] = deck
                _card["txid"] = ct["txid"]
                _card["blockhash"] = ct["blockhash"]
                _card["timestamp"] = ct["time"]
                _card["sender"] = find_tx_sender(provider, ct["txid"])
                _card["asset_specific_data"] = raw_card["asset_specific_data"]

                vouts = provider.getrawtransaction(ct["txid"], 1)["vout"]

                if len(raw_card["amount"]) > 1: ## if card states multiple outputs:
                    for am, v in zip(raw_card["amount"], vouts[2:]):
                        c = _card.copy()
                        c["amount"] = am
                        c["receivers"] = v["scriptPubKey"]["addresses"][0]
                        cards.append(CardTransfer(**c))
                else:
                    _card["receivers"] = vouts[2]["scriptPubKey"]["addresses"][0]
                    _card["amount"] = raw_card["amount"][0]
                    cards.append(CardTransfer(**_card))

        except AssertionError:
            pass

    return cards


class CardTransfer:

    def __init__(self, deck, receivers=[], amount=[], version=1, txid=None, sender=None, blockhash=None,
                 timestamp=None, asset_specific_data="", number_of_decimals=None):
        '''CardTransfer object, used when parsing card_transfers from the blockchain
        or when sending out new card_transfer.
        It can be initialized by passing the **kwargs and it will do the parsing,
        or it can be initialized with passed arguments.
        It requires instance of Deck object as an argument.'''

        self.version = version
        self.deck_id = deck.asset_id
        self.txid = txid
        self.sender = sender
        self.receivers = receivers
        self.amount = amount
        assert len(self.amount) == len(self.receivers), {"error": "Amounts must match receivers."}
        if blockhash:
            self.blockhash = blockhash
        else:
            self.blockhash = "Unconfirmed."
        self.timestamp = timestamp
        self.asset_specific_data = asset_specific_data
        self.p2th_address = deck.p2th_address
        if not number_of_decimals:
            self.number_of_decimals = deck.number_of_decimals

        assert str(self.amount)[::-1].find('.') <= deck.number_of_decimals, {"error": "Too many decimals."}

        if self.sender == deck.issuer:
            self.type = "CardIssue"
        elif self.receivers[0] == deck.issuer:
            self.type = "CardBurn"
        else:
            self.type = "CardTransfer"

    @property
    def metainfo_to_protobuf(self):
        '''encode card_transfer info to protobuf'''

        card = paproto.CardTransfer()
        card.version = self.version
        card.number_of_decimals = self.number_of_decimals
        card.asset_specific_data = self.asset_specific_data.encode()
        for i in self.amount:
            card.amounts.append(i)

        proto = card.SerializeToString()

        if len(proto) > 80:
            warnings.warn('\nMetainfo size exceeds maximum of 80bytes that fit into OP_RETURN.')

        return proto

def card_issue(deck, card_transfer, inputs, change_address, testnet=True, prod=True):
    '''issue cards for this deck
        Arguments:
        * deck - Deck object
        * card_transfer - CardTransfer object
        * inputs - utxo [has to be owned by deck issuer]
        * network - ppc/tppc
        * testnet - True/False
        * prod - production P2TH tag [True/False]
    '''

    issuer_error = {"error": "You must provide UTXO owned by the issuer of this deck."}

    for utxo in inputs["utxos"]:
        assert utxo["address"] == deck.issuer, issuer_error

    if testnet:
        p2th_fee = constants.testnet_p2th_fee
        network = "tppc"
    else:
        p2th_fee = constants.mainnet_p2th_fee
        network = "ppc"

    tx_fee = float(0.01) ## make it static for now, make proper logic later

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": p2th_fee, "outputScript": transactions.monosig_script(deck.p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(card_transfer.metainfo_to_protobuf)}
    ]

    for addr in card_transfer.receivers:
        outputs.append({"redeem": 0, "outputScript": transactions.monosig_script(addr)
                       })

    outputs.append(
        {"redeem": float(inputs['total']) - float(tx_fee) - float(p2th_fee),
         "outputScript": transactions.monosig_script(change_address)
        })

    return transactions.make_raw_transaction(network, inputs['utxos'], outputs)

def card_burn(deck, card_transfer, inputs, change_address, testnet=True, prod=True):
    '''card burn transaction, cards are burned by sending the cards back to deck issuer'''

    assert deck.issuer in card_transfer.receivers, {"error": "One of the recipients must be deck issuer."}

    if testnet:
        p2th_fee = constants.testnet_p2th_fee
        network = "tppc"
    else:
        p2th_fee = constants.mainnet_p2th_fee
        network = "ppc"

    tx_fee = float(0.01) ## make it static for now, make proper logic later

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": p2th_fee, "outputScript": transactions.monosig_script(deck.p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(card_transfer.metainfo_to_protobuf)}
    ]

    for addr in card_transfer.receivers:
        outputs.append({"redeem": 0, "outputScript": transactions.monosig_script(addr)
                       })

    outputs.append(
        {"redeem": float(inputs['total']) - float(tx_fee) - float(p2th_fee),
         "outputScript": transactions.monosig_script(change_address)
        })

    return transactions.make_raw_transaction(network, inputs['utxos'], outputs)

def card_transfer(deck, card_transfer, inputs, change_address, testnet=True, prod=True):
    '''standard peer-to-peer card transfer.'''

    if testnet:
        p2th_fee = constants.testnet_p2th_fee
        network = "tppc"
    else:
        p2th_fee = constants.mainnet_p2th_fee
        network = "ppc"

    tx_fee = float(0.01) ## make it static for now, make proper logic later

    for utxo in inputs['utxos']:
        utxo['txid'] = unhexlify(utxo['txid'])
        utxo['scriptSig'] = unhexlify(utxo['scriptSig'])

    outputs = [
        {"redeem": p2th_fee, "outputScript": transactions.monosig_script(deck.p2th_address)},
        {"redeem": 0, "outputScript": transactions.op_return_script(card_transfer.metainfo_to_protobuf)}
    ]

    for addr in card_transfer.receivers:
        outputs.append({"redeem": 0, "outputScript": transactions.monosig_script(addr)
                       })

    outputs.append(
        {"redeem": float(inputs['total']) - float(tx_fee) - float(p2th_fee),
         "outputScript": transactions.monosig_script(change_address)
        })

    return transactions.make_raw_transaction(network, inputs['utxos'], outputs)

