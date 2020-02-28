
'''miscellaneous utilities.'''

from pypeerassets.provider import Provider, RpcNode, Cryptoid, Blockbook

from pypeerassets.exceptions import (InvalidDeckSpawn,
                                     InvalidDeckMetainfo,
                                     InvalidDeckIssueMode,
                                     InvalidDeckVersion,
                                     InvalidNulldataOutput,
                                     InvalidCardIssue,
                                     DeckP2THImportError,
                                     P2THImportFailed)

from pypeerassets.exceptions import (InvalidCardTransferP2TH,
                                     CardVersionMismatch,
                                     CardNumberOfDecimalsMismatch,
                                     RecieverAmountMismatch
                                     )

from google.protobuf.message import DecodeError
from pypeerassets.pa_constants import param_query
from typing import Iterable, Iterator, Optional, Tuple, List

from pypeerassets.paproto_pb2 import DeckSpawn as DeckSpawnProto
from pypeerassets.paproto_pb2 import CardTransfer as CardTransferProto
from pypeerassets.protocol import Deck, CardTransfer, CardBundle


def load_p2th_privkey_into_local_node(provider: RpcNode, prod: bool=True) -> None:
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


def find_tx_sender(provider: Provider, raw_tx: dict) -> str:
    '''find transaction sender, vin[0] is used in this case.'''

    vin = raw_tx["vin"][0]
    txid = vin["txid"]
    index = vin["vout"]
    return provider.getrawtransaction(txid, 1)["vout"][index]["scriptPubKey"]["addresses"][0]


def find_deck_spawns(provider: Provider, prod: bool=True) -> Iterable[str]:
    '''find deck spawn transactions via Provider,
    it requires that Deck spawn P2TH were imported in local node or
    that remote API knows about P2TH address.'''

    pa_params = param_query(provider.network)

    if isinstance(provider, RpcNode):

        if prod:
            decks = (i["txid"] for i in provider.listtransactions("PAPROD"))
        else:
            decks = (i["txid"] for i in provider.listtransactions("PATEST"))

    if isinstance(provider, Cryptoid) or isinstance(provider, Blockbook):

        if prod:
            decks = (i for i in provider.listtransactions(pa_params.P2TH_addr))
        else:
            decks = (i for i in provider.listtransactions(pa_params.test_P2TH_addr))

    return decks


def deck_parser(args: Tuple[Provider, dict, int, str],
                prod: bool=True) -> Optional[Deck]:
    '''deck parser function'''

    provider = args[0]
    raw_tx = args[1]
    deck_version = args[2]
    p2th = args[3]

    try:
        validate_deckspawn_p2th(provider, raw_tx, p2th)

        d = parse_deckspawn_metainfo(read_tx_opreturn(raw_tx['vout'][1]),
                                     deck_version)

        if d:

            d["id"] = raw_tx["txid"]
            try:
                d["issue_time"] = raw_tx["blocktime"]
            except KeyError:
                d["issue_time"] = 0
            d["issuer"] = find_tx_sender(provider, raw_tx)
            d["network"] = provider.network
            d["production"] = prod
            try:
                d["tx_confirmations"] = raw_tx["confirmations"]
            except KeyError:
                d["tx_confirmations"] = 0
            return Deck(**d)

    except (InvalidDeckSpawn, InvalidDeckMetainfo, InvalidDeckVersion,
            InvalidNulldataOutput) as err:
        pass

    return None


def tx_serialization_order(provider: Provider, blockhash: str, txid: str) -> int:
    '''find index of this tx in the blockid'''

    return provider.getblock(blockhash)["tx"].index(txid)


def read_tx_opreturn(vout: dict) -> bytes:
    '''Decode OP_RETURN message from vout[1]'''

    asm = vout['scriptPubKey']['asm']
    n = asm.find('OP_RETURN')
    if n == -1:
        raise InvalidNulldataOutput({'error': 'OP_RETURN not found.'})
    else:
        # add 10 because 'OP_RETURN ' is 10 characters
        n += 10
        data = asm[n:]
        n = data.find(' ')
        # make sure that we don't include trailing opcodes
        if n == -1:
            return bytes.fromhex(data)
        else:
            return bytes.fromhex(data[:n])


def deck_issue_mode(proto: DeckSpawnProto) -> Iterable[str]:
    '''interpret issue mode bitfeg'''

    if proto.issue_mode == 0:
        yield "NONE"
        return

    for mode, value in proto.MODE.items():
        if value > proto.issue_mode:
            continue
        if value & proto.issue_mode:
            yield mode


def issue_mode_to_enum(deck: DeckSpawnProto, issue_mode: list) -> int:
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

    deck = DeckSpawnProto()
    deck.ParseFromString(protobuf)

    error = {"error": "Deck ({deck}) metainfo incomplete, deck must have a name.".format(deck=deck.name)}

    if deck.name == "":
        raise InvalidDeckMetainfo(error)

    if deck.version != version:
        raise InvalidDeckVersion({"error", "Deck version mismatch."})

    return {
        "version": deck.version,
        "name": deck.name,
        "issue_mode": deck.issue_mode,
        "number_of_decimals": deck.number_of_decimals,
        "asset_specific_data": deck.asset_specific_data
        }


def validate_deckspawn_p2th(provider: Provider, rawtx: dict, p2th: str) -> bool:
    '''Return True if deck spawn pays to p2th in vout[0] and if the P2TH address
    is correct. Otherwise raises InvalidDeckSpawn.
    '''

    try:
        vout = rawtx["vout"][0]["scriptPubKey"].get("addresses")[0]
    except TypeError:
        '''TypeError: 'NoneType' object is not subscriptable error on some of the deck spawns.'''
        raise InvalidDeckSpawn("Invalid Deck P2TH.")

    if not vout == p2th:
        raise InvalidDeckSpawn("InvalidDeck P2TH.")

    return True


def load_deck_p2th_into_local_node(provider: RpcNode, deck: Deck) -> None:
    '''
    load deck p2th into local node via "importprivke",
    this allows building of proof-of-timeline for this deck
    '''

    assert isinstance(provider, RpcNode), {"error": "You can load privkeys only into local node."}
    error = {"error": "Deck P2TH import went wrong."}

    provider.importprivkey(deck.p2th_wif, deck.id)
    check_addr = provider.validateaddress(deck.p2th_address)

    if not check_addr["isvalid"] and not check_addr["ismine"]:
        raise DeckP2THImportError(error)


def validate_card_transfer_p2th(deck: Deck, vout: dict) -> None:
    '''validate if card_transfer transaction pays to deck p2th in vout[0]'''

    error = {"error": "Card transfer is not properly tagged."}

    try:
        address = vout["scriptPubKey"].get("addresses")[0]
        if not address == deck.p2th_address:
            raise InvalidCardTransferP2TH(error)
    except TypeError as e:
        raise e


def parse_card_transfer_metainfo(protobuf: bytes, deck_version: int) -> dict:
    '''decode card_spawn protobuf message and validate it against deck.version
    :protobuf - bytes from op_return message
    :deck_version - integer
    '''

    card = CardTransferProto()
    card.ParseFromString(protobuf)

    if not card.version == deck_version:
        raise CardVersionMismatch({'error': 'card version does not match deck version.'})

    return {
        "version": card.version,
        "number_of_decimals": card.number_of_decimals,
        "amount": list(card.amount),
        "asset_specific_data": card.asset_specific_data
    }


def card_postprocess(card: dict, vout: list) -> List[dict]:

    # if card states multiple outputs, interpert it as a batch
    if len(card["amount"]) > 1:
        cards = []
        for am, v in zip(card["amount"], vout[2:]):
            c = card.copy()
            c["amount"] = [am]
            c["receiver"] = v["scriptPubKey"]["addresses"]
            c["cardseq"] = vout[2:].index(v)

            cards.append(c)
        return cards

    else:
        card["receiver"] = vout[2]["scriptPubKey"]["addresses"]
        card["cardseq"] = 0

    return [card]


def card_bundle_parser(bundle: CardBundle, debug=False) -> Iterator:
    '''this function wraps all the card transfer parsing'''

    try:
        # first vout of the bundle must pay to deck.p2th
        validate_card_transfer_p2th(bundle.deck, bundle.vouts[0])

        # second vout must be OP_RETURN with card_metainfo
        card_metainfo = parse_card_transfer_metainfo(
                            read_tx_opreturn(bundle.vouts[1]),
                            bundle.deck.version
                            )

    # if any of this exceptions is raised, return None
    except (InvalidCardTransferP2TH,
            CardVersionMismatch,
            CardNumberOfDecimalsMismatch,
            RecieverAmountMismatch,
            DecodeError,
            TypeError,
            InvalidNulldataOutput) as e:

        if debug:
            print(e)  # re-do as logging later on
        return
        yield

    # check for decimals
    if not card_metainfo["number_of_decimals"] == bundle.deck.number_of_decimals:
        raise CardNumberOfDecimalsMismatch(
                {"error": "Number of decimals does not match."}
                )

    # deduce the individual cards in the bundle
    cards = card_postprocess(card_metainfo, bundle.vouts)

    #  drop the vouts property
    del bundle.__dict__['vouts']

    for c in cards:
        d = {**c, **bundle.__dict__}

        try:
            yield CardTransfer(**d)

        # issuing cards to issuing address is forbidden,
        # this will except the error
        except InvalidCardIssue as e:

            if debug:
                print(e)


def amount_to_exponent(amount: float, number_of_decimals: int) -> int:
    '''encode amount integer as exponent'''

    return int(amount * 10**number_of_decimals)


def exponent_to_amount(exponent: int, number_of_decimals: int) -> float:
    '''exponent to integer to be written on the chain'''

    return exponent / 10**number_of_decimals
