
'''miscellaneous utilities.'''

import binascii
from .provider import *
from .constants import param_query, params
from typing import Iterator
from .paproto import DeckSpawn, CardTransfer
from . import paproto


def load_p2th_privkeys_into_local_node(provider: RpcNode, prod=True) -> None:
    '''load production p2th privkey into local node'''

    assert isinstance(provider, RpcNode), {"error": "Import only works with local node."}
    error = {"error": "Loading P2TH privkey failed."}
    pa_params = param_query(provider.network)

    if prod:
        provider.importprivkey(pa_params.P2TH_wif, "PAPROD")
        assert isinstance(provider.listtransactions("PAPROD"), list), error
    else:
        provider.importprivkey(pa_params.test_P2TH_wif, "PATEST")
        assert isinstance(provider.listtransactions("PATEST"), list), error


def find_tx_sender(provider, raw_tx: dict) -> str:
    '''find transaction sender, vin[0] is used in this case.'''

    vin = raw_tx["vin"][0]
    txid = vin["txid"]
    index = vin["vout"]
    return provider.getrawtransaction(txid, 1)["vout"][index]["scriptPubKey"]["addresses"][0]


def find_deck_spawns(provider, prod=True):
    '''find deck spawn transactions via provider,
    it requires that Deck spawn P2TH were imported in local node or
    that remote API knows about P2TH address.'''

    pa_params = param_query(provider.network)

    if isinstance(provider, RpcNode):

        if prod:
            decks = (i["txid"] for i in provider.listtransactions("PAPROD"))
        else:
            decks = (i["txid"] for i in provider.listtransactions("PATEST"))

    if isinstance(provider, Mintr):

        if prod:
            decks = (i["txid"] for i in provider.listtransactions(pa_params.P2TH_addr))
        else:
            raise NotImplementedError

    if isinstance(provider, Holy):

        if prod:
            decks = (i for i in provider.listtransactions(pa_params.P2TH_addr))
        else:
            decks = (i for i in provider.listtransactions(pa_params.test_P2TH_addr))

    return decks


def tx_serialization_order(provider, blockhash: str, txid: str) -> int:
    '''find index of this tx in the blockid'''

    return provider.getblock(blockhash)["tx"].index(txid)


def read_tx_opreturn(raw_tx: dict) -> bytes:
    '''Decode OP_RETURN message from raw_tx'''

    vout = raw_tx['vout'][1]  # PA protocol requires that OP_RETURN is vout[1]

    asm = vout['scriptPubKey']['asm']
    n = asm.find('OP_RETURN')
    if n == -1:
        return False #{'error': 'OP_RETURN not found'}
    else:
        # add 10 because 'OP_RETURN ' is 10 characters
        n += 10
        data = asm[n:]
        n = data.find(' ')
        #make sure that we don't include trailing opcodes
        if n == -1:
            return binascii.unhexlify(data)
        else:
            return binascii.unhexlify(data[:n])


def deck_issue_mode_logic_check(issue_mode):
    '''verify do combined issue modes pass simple logic tests'''
    raise NotImplementedError


def deck_issue_mode(proto: DeckSpawn) -> Iterator[str]:
    '''interpret issue mode bitfeg'''

    for mode in proto.MODE.keys():
        if proto.issue_mode & proto.MODE.Value(mode):
            yield mode


def issue_mode_to_enum(deck: DeckSpawn, issue_mode: list) -> int:
    '''encode issue mode(s) as bitfeg'''

    # case where there are multiple issue modes specified
    if isinstance(issue_mode, list) and len(issue_mode) > 1:
        r = 0
        for mode in issue_mode:
            r += deck.MODE.Value(mode)
        return r

    if isinstance(issue_mode, str):  # if single issue mode
        return deck.MODE.Value(issue_mode)

    else:
        return {'error': 'issue_mode given in wrong format.'}


def parse_deckspawn_metainfo(protobuf: bytes) -> dict:
    '''decode deck_spawn tx op_return protobuf message and validate it.'''

    deck = paproto.DeckSpawn()
    deck.ParseFromString(protobuf)

    assert deck.name is not "", {"error": "Deck metainfo incomplete, Deck must have a name."}

    return {
        "version": deck.version,
        "name": deck.name,
        "issue_mode": list(deck_issue_mode(deck)),
        "number_of_decimals": deck.number_of_decimals,
        "asset_specific_data": deck.asset_specific_data
    }


def validate_deckspawn_p2th(provider, raw_tx, prod=True):
    '''validate if deck spawn pays to p2th in vout[0] and if it correct P2TH address'''

    pa_params = param_query(provider.network)
    vout = raw_tx["vout"][0]["scriptPubKey"].get("addresses")[0]
    error = {"error": "This deck is not properly tagged."}

    if prod:
        assert vout == pa_params.P2TH_addr, error
        return True
    else:
        assert vout == pa_params.test_P2TH_addr, error
        return True


def load_deck_p2th_into_local_node(provider, deck) -> None:
    '''
    load deck p2th into local node,
    this allows building of proof-of-timeline for this deck
    '''

    assert isinstance(provider, RpcNode), {"error": "You can load privkeys only into local node."}
    error = {"error": "Deck P2TH import went wrong."}

    provider.importprivkey(deck.p2th_wif, deck.name)
    check_addr = provider.validateaddress(deck.p2th_address)
    assert check_addr["isvalid"] and check_addr["ismine"], error


def validate_card_transfer_p2th(deck, raw_tx: dict) -> None:
    '''validate if card_transfer transaction pays to deck p2th in vout[0]'''

    error = {"error": "Card transfer is not properly tagged."}

    assert raw_tx["vout"][0]["scriptPubKey"].get("addresses")[0] == deck.p2th_address, error


def parse_card_transfer_metainfo(protobuf: bytes) -> dict:
    '''decode card_spawn tx op_return protobuf message and validate it.'''

    card = paproto.CardTransfer()
    card.ParseFromString(protobuf)

    assert card.version > 0, {"error": "Card metainfo incomplete, version can't be 0."}

    return {
        "version": card.version,
        "number_of_decimals": card.number_of_decimals,
        "amount": card.amount,
        "asset_specific_data": card.asset_specific_data
    }


def postprocess_card(card_metainfo: CardTransfer, raw_tx: dict, sender: str,
                     vout: list, blockseq: int, blocknum: int, deck) -> list:
    '''Postprocessing of all the relevant card transfer information and
    the creation of CardTransfer object.

    : card_metainfo: card_transfer protobuf
    : raw_tx: raw transaction
    : sender: tx sender
    : vout: tx vout
    : blockseq: tx block sequence number
    : blocknum: block number
    : deck: deck object this card transfer belongs to'''

    card_metainfo = parse_card_transfer_metainfo(card_metainfo)
    nderror = {"error": "Number of decimals does not match."}

    _card = {}
    _card["version"] = card_metainfo["version"]
    _card["number_of_decimals"] = card_metainfo["number_of_decimals"]
    try:  # check if card number of decimals matches the deck atribute
        assert _card["number_of_decimals"] == deck.number_of_decimals, nderror
    except AssertionError:
        return

    _card["deck"] = deck
    _card["txid"] = raw_tx["txid"]
    try:
        _card["blockhash"] = raw_tx["blockhash"]
    except KeyError:
        _card["blockhash"] = 0
    if blockseq:
        _card["blockseq"] = blockseq
    if blocknum:
        _card["blocknum"] = blocknum
    _card["timestamp"] = raw_tx["time"]
    _card["sender"] = sender
    _card["asset_specific_data"] = card_metainfo["asset_specific_data"]

    if len(card_metainfo["amount"]) > 1:  # if card states multiple outputs:
        cards = []
        for am, v in zip(card_metainfo["amount"], vout[2:]):
            c = _card.copy()
            c["amount"] = [am]
            c["receiver"] = v["scriptPubKey"]["addresses"]
            c["cardseq"] = vout[2:].index(v)

            cards.append(c)
        return cards
    else:
        _card["receiver"] = vout[2]["scriptPubKey"]["addresses"]
        _card["amount"] = card_metainfo["amount"]
        _card["cardseq"] = 0

    return [_card]


def amount_to_exponent(amount: float, number_of_decimals: int) -> int:
    '''encode amount integer as exponent'''

    return int(amount * 10**number_of_decimals)


def exponent_to_amount(exponent: int, number_of_decimals: int) -> float:
    '''exponent to integer to be written on the chain'''

    return exponent / 10**number_of_decimals
