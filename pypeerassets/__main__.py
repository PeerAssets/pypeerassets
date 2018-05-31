
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

import concurrent.futures
from typing import Generator, Tuple, Optional
from pypeerassets.protocol import Deck, CardTransfer, validate_card_issue_modes
from .provider import Provider, RpcNode
from pypeerassets.pautils import (find_tx_sender,
                                  find_deck_spawns, tx_serialization_order,
                                  read_tx_opreturn,
                                  parse_deckspawn_metainfo,
                                  validate_deckspawn_p2th,
                                  validate_card_transfer_p2th,
                                  parse_card_transfer_metainfo,
                                  postprocess_card
                                  )
#from .voting import *
from .exceptions import *
from .transactions import (nulldata_script, tx_output, p2pkh_script,
                           find_parent_outputs,
                           make_raw_transaction,
                           Transaction)
from .pa_constants import param_query
from .networks import net_query
from decimal import Decimal, getcontext
getcontext().prec = 6


def deck_parser(args: Tuple[Provider, dict, int, str], prod: bool=True) -> Optional[Deck]:
    '''deck parser function'''

    provider = args[0]
    raw_tx = args[1]
    deck_version = args[2]
    p2th = args[3]

    try:
        validate_deckspawn_p2th(provider, raw_tx, p2th)

        d = parse_deckspawn_metainfo(read_tx_opreturn(raw_tx), deck_version)

        if d:

            d["id"] = raw_tx["txid"]
            try:
                d["time"] = raw_tx["blocktime"]
            except KeyError:
                d["time"] = 0
            d["issuer"] = find_tx_sender(provider, raw_tx)
            d["network"] = provider.network
            d["production"] = prod
            d["tx_confirmations"] = raw_tx["confirmations"]
            return Deck(**d)

    except (InvalidDeckSpawn, InvalidDeckMetainfo, InvalidDeckVersion, InvalidNulldataOutput) as err:
        pass

    return None


def find_all_valid_decks(provider: Provider, deck_version: int, prod: bool=True) -> Generator:
    '''
    Scan the blockchain for PeerAssets decks, returns list of deck objects.
    : provider - provider instance
    : version - deck protocol version (0, 1, 2, ...)
    : test True/False - test or production P2TH
    '''

    pa_params = param_query(provider.network)

    if prod:
        p2th = pa_params.P2TH_addr
    else:
        p2th = pa_params.test_P2TH_addr

    if isinstance(provider, RpcNode):
        deck_spawns = (provider.getrawtransaction(i, 1) for i in find_deck_spawns(provider))

    else:
        try:
            deck_spawns = (provider.getrawtransaction(i, 1) for i in
                           provider.listtransactions(p2th))
        except TypeError as err:  # it will except if no transactions are found on this P2TH
            raise EmptyP2THDirectory(err)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as th:
        for result in th.map(deck_parser, ((provider, rawtx, deck_version, p2th) for rawtx in deck_spawns)):
            if result:
                yield result


def find_deck(provider: Provider, key: str, version: int, prod: bool=True) -> Optional[Deck]:
    '''Find specific deck by deck id.'''

    pa_params = param_query(provider.network)
    if prod:
        p2th = pa_params.P2TH_addr
    else:
        p2th = pa_params.test_P2TH_addr

    rawtx = provider.getrawtransaction(key, 1)
    deck = deck_parser((provider, rawtx, 1, p2th))

    return deck


def deck_spawn(provider: Provider, deck: Deck, inputs: dict,
               change_address: str) -> Transaction:
    '''Creates Deck spawn raw transaction.
       : key - Kutil object which we'll use to sign the tx
       : deck - Deck object
       : card - CardTransfer object
       : inputs - utxos (has to be owned by deck issuer)
       : change_address - address to send the change to
    '''

    network_params = net_query(deck.network)
    pa_params = param_query(deck.network)

    if deck.production:
        p2th_addr = pa_params.P2TH_addr
    else:
        p2th_addr = pa_params.test_P2TH_addr

    #  first round of txn making is done by presuming minimal fee
    change_sum = Decimal(inputs['total'] - network_params.min_tx_fee - pa_params.P2TH_fee)

    txouts = [
        tx_output(value=pa_params.P2TH_fee, n=0, script=p2pkh_script(p2th_addr)),  # p2th
        tx_output(value=Decimal(0), n=1, script=nulldata_script(deck.metainfo_to_protobuf)),  # op_return
        tx_output(value=change_sum, n=2, script=p2pkh_script(change_address))  # change
              ]

    unsigned_tx = make_raw_transaction(inputs['utxos'], txouts)
    return unsigned_tx


def deck_transfer(provider: Provider, deck: Deck,
                  inputs: list, change_address: str) -> Transaction:
    '''
    The deck transfer transaction is a special case of the deck spawn transaction.
    Instead of registering a new asset, the deck transfer transaction transfers ownership from vin[1] to vin[0],
    meaning that both parties are required to sign the transfer transaction for it to be accepted in the blockchain.
    '''
    raise NotImplementedError


def get_card_transfers(provider: Provider, deck: Deck) -> Generator:
    '''get all <deck> card transfers, if cards match the protocol'''

    if isinstance(provider, RpcNode):
        if deck.id is None:
            raise Exception("deck.id required to listtransactions")
        batch_data = [('getrawtransaction', [i["txid"], 1] ) for i in provider.listtransactions(deck.id)]
        result = provider.batch(batch_data)
        if result is not None:
            card_transfers = [i['result'] for i in result if result]
    else:
        if deck.p2th_address is None:
            raise Exception("deck.p2th_address required to listtransactions")
        if provider.listtransactions(deck.p2th_address):
            card_transfers = (provider.getrawtransaction(i, 1) for i in
                              provider.listtransactions(deck.p2th_address))
        else:
            raise EmptyP2THDirectory({'error': 'No cards found on this deck.'})

    def card_parser(args: Tuple[Provider, Deck, dict]) -> list:
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
                blockseq = 0
            try:  # try to get block number of block when this tx was written
                blocknum = provider.getblock(raw_tx["blockhash"])["height"]
            except KeyError:
                blocknum = 0
            try:  # try to get tx confirmation count
                tx_confirmations = raw_tx["confirmations"]
            except KeyError:
                tx_confirmations = 0

            cards = postprocess_card(card_metainfo, raw_tx, sender,
                                     vouts, blockseq, blocknum,
                                     tx_confirmations, deck)
            cards = [CardTransfer(**card) for card in cards]

        except (InvalidCardTransferP2TH, CardVersionMismatch,
                CardNumberOfDecimalsMismatch, InvalidVoutOrder,
                RecieverAmountMismatch) as e:
            return []

        return cards

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as th:
        for result in th.map(card_parser, ((provider, deck, i) for i in card_transfers)):
            if result:
                yield result


def find_all_valid_cards(provider: Provider, deck: Deck) -> Generator:
    '''find all the valid cards on this deck,
       filtering out cards which don't play nice with deck issue mode'''

    # validate_card_issue_modes must recieve a full list of cards, not batches
    unfiltered = (card for batch in get_card_transfers(provider, deck) for card in batch)

    for card in validate_card_issue_modes(deck.issue_mode, list(unfiltered)):
        yield card


def card_transfer(provider: Provider, card: CardTransfer, inputs: dict,
                  change_address: str) -> Transaction:
    '''Prepare the CardTransfer Transaction object
       : card - CardTransfer object
       : inputs - utxos (has to be owned by deck issuer)
       : change_address - address to send the change to
       '''

    network_params = net_query(provider.network)
    pa_params = param_query(provider.network)

    if card.deck_p2th is None:
        raise Exception("card.deck_p2th required for tx_output")

    outs = [
        tx_output(value=pa_params.P2TH_fee, n=0, script=p2pkh_script(card.deck_p2th)),  # deck p2th
        tx_output(value=Decimal(0), n=1, script=nulldata_script(card.metainfo_to_protobuf))  # op_return
    ]

    for addr, index in zip(card.receiver, range(len(card.receiver))):
        outs.append(   # TxOut for each receiver, index + 2 because we have two outs already
            tx_output(value=Decimal(0), n=index+2, script=p2pkh_script(addr))
        )

    #  first round of txn making is done by presuming minimal fee
    change_sum = Decimal(inputs['total'] - network_params.min_tx_fee - pa_params.P2TH_fee)

    outs.append(
        tx_output(value=change_sum, n=len(outs)+1, script=p2pkh_script(change_address))
        )

    unsigned_tx = make_raw_transaction(inputs['utxos'], outs)
    return unsigned_tx
