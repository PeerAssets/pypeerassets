
'''contains main protocol logic like assembly of proof-of-timeline and parsing deck info'''

import concurrent.futures
from typing import Iterator, Generator, Optional

from pypeerassets.protocol import (Deck,
                                   CardBundle,
                                   CardTransfer,
                                   validate_card_issue_modes
                                   )

from pypeerassets.provider import Provider, RpcNode

from pypeerassets.pautils import (deck_parser,
                                  find_deck_spawns,
                                  card_bundle_parser,
                                  tx_serialization_order,
                                  find_tx_sender
                                  )

from pypeerassets.exceptions import EmptyP2THDirectory

from pypeerassets.transactions import (nulldata_script, tx_output,
                                       p2pkh_script,
                                       make_raw_transaction,
                                       Transaction,
                                       Locktime)

from pypeerassets.pa_constants import param_query
from pypeerassets.networks import net_query
from decimal import Decimal


def find_all_valid_decks(provider: Provider, deck_version: int,
                         prod: bool=True) -> Generator:
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
        deck_spawns = (provider.getrawtransaction(i, 1)
                       for i in find_deck_spawns(provider))

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
               change_address: str, locktime: int=0) -> Transaction:

    '''Creates Deck spawn raw transaction.

       : key - Kutil object which we'll use to sign the tx
       : deck - Deck object
       : card - CardTransfer object
       : inputs - utxos (has to be owned by deck issuer)
       : change_address - address to send the change to
       : locktime - tx locked until block n=int
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
        tx_output(network=deck.network, value=pa_params.P2TH_fee,
                  n=0, script=p2pkh_script(address=p2th_addr,
                                           network=deck.network)),  # p2th

        tx_output(network=deck.network, value=Decimal(0),
                  n=1, script=nulldata_script(deck.metainfo_to_protobuf)),  # op_return

        tx_output(network=deck.network, value=change_sum,
                  n=2, script=p2pkh_script(address=change_address,
                                           network=deck.network))  # change
              ]

    unsigned_tx = make_raw_transaction(network=deck.network,
                                       inputs=inputs['utxos'],
                                       outputs=txouts,
                                       locktime=Locktime(locktime)
                                       )
    return unsigned_tx


def deck_transfer(provider: Provider, deck: Deck,
                  inputs: list, change_address: str) -> Transaction:
    '''
    The deck transfer transaction is a special case of the deck spawn transaction.
    Instead of registering a new asset, the deck transfer transaction transfers ownership from vin[1] to vin[0],
    meaning that both parties are required to sign the transfer transaction for it to be accepted in the blockchain.
    '''
    raise NotImplementedError


def card_bundler(provider: Provider, deck: Deck, tx: dict) -> CardBundle:
    '''each blockchain transaction can contain multiple cards,
       wrapped in bundles. This method finds and returns those bundles.'''

    return CardBundle(deck=deck,
                      blockhash=tx['blockhash'],
                      txid=tx['txid'],
                      timestamp=tx['time'],
                      blockseq=tx_serialization_order(provider,
                                                      tx["blockhash"],
                                                      tx["txid"]),
                      blocknum=provider.getblock(tx["blockhash"])["height"],
                      sender=find_tx_sender(provider, tx),
                      vouts=tx['vout'],
                      tx_confirmations=tx['confirmations']
                      )


def find_card_bundles(provider: Provider, deck: Deck) -> Optional[Iterator]:
    '''each blockchain transaction can contain multiple cards,
       wrapped in bundles. This method finds and returns those bundles.'''

    if isinstance(provider, RpcNode):
        if deck.id is None:
            raise Exception("deck.id required to listtransactions")

        batch_data = [('getrawtransaction', [i["txid"], 1]) for
                      i in provider.listtransactions(deck.id)]
        result = provider.batch(batch_data)

        if result is not None:
            raw_txns = [i['result'] for i in result if result]

        else:
            raise EmptyP2THDirectory({'error': 'No cards found on this deck.'})

    else:
        if deck.p2th_address is None:
            raise Exception("deck.p2th_address required to listtransactions")

        try:
            raw_txns = (provider.getrawtransaction(i, 1) for i in
                        provider.listtransactions(deck.p2th_address))
        except TypeError:
            raise EmptyP2THDirectory({'error': 'No cards found on this deck.'})

    return (card_bundler(provider, deck, i) for i in raw_txns)


def get_card_bundles(provider: Provider, deck: Deck) -> Generator:
    '''get all <deck> card bundles, if they match the protocol'''

    bundles = find_card_bundles(provider, deck)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as th:
        for result in th.map(card_bundle_parser, bundles):
            if result:
                yield result


def get_card_transfer(provider: Provider, deck: Deck,
                      txid: str,
                      debug: bool=False) -> Iterator:
    '''get a single card transfer by it's id'''

    rawtx = provider.getrawtransaction(txid, 1)

    bundle = card_bundler(provider, deck, rawtx)

    return card_bundle_parser(bundle, debug)


def find_all_valid_cards(provider: Provider, deck: Deck) -> Generator:
    '''find all the valid cards on this deck,
       filtering out cards which don't play nice with deck issue mode'''

    # validate_card_issue_modes must recieve a full list of cards, not batches
    unfiltered = (card for batch in get_card_bundles(provider, deck) for card in batch)

    for card in validate_card_issue_modes(deck.issue_mode, list(unfiltered)):
        yield card


def card_transfer(provider: Provider, card: CardTransfer, inputs: dict,
                  change_address: str, locktime: int=0) -> Transaction:

    '''Prepare the CardTransfer Transaction object

       : card - CardTransfer object
       : inputs - utxos (has to be owned by deck issuer)
       : change_address - address to send the change to
       : locktime - tx locked until block n=int
       '''

    network_params = net_query(provider.network)
    pa_params = param_query(provider.network)

    if card.deck_p2th is None:
        raise Exception("card.deck_p2th required for tx_output")

    outs = [
        tx_output(network=provider.network,
                  value=pa_params.P2TH_fee,
                  n=0, script=p2pkh_script(address=card.deck_p2th,
                                           network=provider.network)),  # deck p2th
        tx_output(network=provider.network,
                  value=Decimal(0), n=1,
                  script=nulldata_script(card.metainfo_to_protobuf))  # op_return
    ]

    for addr, index in zip(card.receiver, range(len(card.receiver))):
        outs.append(   # TxOut for each receiver, index + 2 because we have two outs already
            tx_output(network=provider.network, value=Decimal(0), n=index+2,
                      script=p2pkh_script(address=addr,
                                          network=provider.network))
        )

    #  first round of txn making is done by presuming minimal fee
    change_sum = Decimal(inputs['total'] - network_params.min_tx_fee - pa_params.P2TH_fee)

    outs.append(
        tx_output(network=provider.network,
                  value=change_sum, n=len(outs)+1,
                  script=p2pkh_script(address=change_address,
                                      network=provider.network))
        )

    unsigned_tx = make_raw_transaction(network=provider.network,
                                       inputs=inputs['utxos'],
                                       outputs=outs,
                                       locktime=Locktime(locktime)
                                       )
    return unsigned_tx
