
'''miscellaneous utilities.'''

import binascii
from .provider import *
from .exceptions import P2THImportFailed
from .exceptions import (InvalidDeckSpawn, InvalidDeckMetainfo,
                         InvalidDeckIssueMode, InvalidDeckVersion)
from .exceptions import (InvalidCardTransferP2TH, CardVersionMistmatch,
                         CardNumberOfDecimalsMismatch)
from .constants import param_query, params
from typing import Iterator
from .paproto import DeckSpawn, CardTransfer
from . import paproto


def load_p2th_privkey_into_local_node(provider: RpcNode, prod=True) -> None:
    '''Load PeerAssets P2TH privkey into the local node.'''

    assert isinstance(provider, RpcNode), {"error": "Import only works with local node."}
    error = {"error": "Loading P2TH privkey failed."}
    pa_params = param_query(provider.network)

    if prod:
        provider.importprivkey(pa_params.P2TH_wif, "PAPROD")
        #  now verify if ismine == True
        if not provider.validateaddress(pa_params.P2TH_addr)['ismine']:
            raise P2THImportFailed(error)
    else:
        provider.importprivkey(pa_params.test_P2TH_wif, "PATEST")
        if not provider.validateaddress(pa_params.test_P2TH_addr)['ismine']:
            raise P2THImportFailed(error)


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

    if isinstance(provider, Holy) or isinstance(provider, Cryptoid):

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

    elif isinstance(issue_mode, str):  # if single issue mode
        return deck.MODE.Value(issue_mode)

    else:
        raise InvalidDeckIssueMode({'error': 'issue_mode given in wrong format.'})


def parse_deckspawn_metainfo(protobuf: bytes, version: int) -> dict:
    '''Decode deck_spawn tx op_return protobuf message and validate it,
       Raise error if deck_spawn metainfo incomplete or version mistmatch.'''

    deck = paproto.DeckSpawn()
    deck.ParseFromString(protobuf)

    error = {"error": "Deck ({deck}) metainfo incomplete, deck must have a name.".format(deck=deck.name)}

    if deck.name == "":
        raise InvalidDeckMetainfo(error)

    if deck.version != version:
        raise InvalidDeckVersion({"error", "Deck version mismatch."})

    return {
        "version": deck.version,
        "name": deck.name,
        "issue_mode": list(deck_issue_mode(deck)),
        "number_of_decimals": deck.number_of_decimals,
        "asset_specific_data": deck.asset_specific_data
    }


def validate_deckspawn_p2th(provider, rawtx, prod=True):
    '''validate if deck spawn pays to p2th in vout[0] and if it correct P2TH address'''

    error = {"Error": "This deck ({deck}) is not properly tagged.".format(deck=rawtx['txid'])}
    pa_params = param_query(provider.network)

    try:
        vout = rawtx["vout"][0]["scriptPubKey"].get("addresses")[0]
    except TypeError:
        '''TypeError: 'NoneType' object is not subscriptable error on some of the deck spawns.'''
        raise InvalidDeckSpawn(error)

    if prod:
        if not vout == pa_params.P2TH_addr:
            raise InvalidDeckSpawn(error)
        return True

    else:
        if not vout == pa_params.test_P2TH_addr:
            raise InvalidDeckSpawn(error)
        return True


def load_deck_p2th_into_local_node(provider, deck) -> None:
    '''
    load deck p2th into local node,
    this allows building of proof-of-timeline for this deck
    '''

    assert isinstance(provider, RpcNode), {"error": "You can load privkeys only into local node."}
    error = {"error": "Deck P2TH import went wrong."}

    provider.importprivkey(deck.p2th_wif, deck.asset_id)
    check_addr = provider.validateaddress(deck.p2th_address)
    assert check_addr["isvalid"] and check_addr["ismine"], error


def validate_card_transfer_p2th(deck, raw_tx: dict) -> None:
    '''validate if card_transfer transaction pays to deck p2th in vout[0]'''

    error = {"error": "Card transfer is not properly tagged."}

    if not raw_tx["vout"][0]["scriptPubKey"].get("addresses")[0] == deck.p2th_address:
        raise InvalidCardTransferP2TH(error)


def parse_card_transfer_metainfo(protobuf: bytes, deck_version: int) -> dict:
    '''decode card_spawn protobuf message and validate it against deck.version'''

    card = paproto.CardTransfer()
    card.ParseFromString(protobuf)

    if not card.version == deck_version:
        raise CardVersionMistmatch({'error': 'card version does not match deck version.'})

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

    nderror = {"error": "Number of decimals does not match."}

    _card = {}
    _card["version"] = card_metainfo["version"]
    _card["number_of_decimals"] = card_metainfo["number_of_decimals"]
    # check if card number of decimals matches the deck atribute
    if not _card["number_of_decimals"] == deck.number_of_decimals:
        raise CardNumberOfDecimalsMismatch(nderror)

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

    return (_card, )


def amount_to_exponent(amount: float, number_of_decimals: int) -> int:
    '''encode amount integer as exponent'''

    return int(amount * 10**number_of_decimals)


def exponent_to_amount(exponent: int, number_of_decimals: int) -> float:
    '''exponent to integer to be written on the chain'''

    return exponent / 10**number_of_decimals
