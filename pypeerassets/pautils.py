
'''miscellaneous utilities.'''

import binascii
from pypeerassets.provider import RpcNode, Mintr
from .constants import param_query, params
from pypeerassets import paproto

def load_p2th_privkeys_into_node(provider, prod=True):
    '''load production p2th privkey into local node'''

    assert isinstance(provider, RpcNode), {"error": "You can load privkeys only into local node."}
    error = {"error": "Loading P2TH privkey failed."}
    pa_params = param_query(provider.network)

    if prod:
        provider.importprivkey(pa_params.P2TH_wif, "PAPROD")
        assert pa_params.P2TH_addr in provider.getaddressesbyaccount("PAPROD"), error

    else:
        provider.importprivkey(pa_params.test_P2TH_wif, "PATEST")
        assert pa_params.test_P2TH_wif in provider.getaddressesbyaccount("PATEST"), error

def find_tx_sender(provider, txid):
    '''find transaction sender, vin[0] is used in this case.'''

    vin = provider.getrawtransaction(txid, 1)["vin"][0]
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
            decks = [i["txid"] for i in provider.listtransactions("PAPROD")]
        else:
            decks = [i["txid"] for i in provider.listtransactions("PATEST")]

        return decks

    if isinstance(provider, Mintr):

        if prod:
            decks = [i["txid"] for i in provider.listtransactions(pa_params.P2TH_addr)]
        else:
            raise NotImplementedError

def read_tx_opreturn(node, txid):
    '''Decode OP_RETURN message from <txid>'''

    vout = node.getrawtransaction(txid, 1)['vout'][1] # protocol requires that OP_RETURN is vout[1]

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

def validate_deckspawn_metainfo(deck):
    '''validate deck_spawn'''

    assert deck.version > 0, {"error": "Deck metainfo incomplete, version can't be 0."}
    assert deck.name is not "", {"error": "Deck metainfo incomplete, Deck must have a name."}
    assert deck.issue_mode in (0, 1, 2, 4), {"error": "Deck metainfo incomplete, unknown issue mode."}

def parse_deckspawn_metainfo(protobuf):
    '''decode deck_spawn tx op_return protobuf message and validate it.'''

    deck = paproto.DeckSpawn()
    deck.ParseFromString(protobuf)

    validate_deckspawn_metainfo(deck)

    return {
        "version": deck.version,
        "name": deck.name,
        "issue_mode": deck.MODE.Name(deck.issue_mode),
        "number_of_decimals": deck.number_of_decimals,
        "asset_specific_data": deck.asset_specific_data
    }

def validate_deckspawn_p2th(provider, deck_id, prod=True):
    '''validate if deck spawn pays to p2th in vout[0] and if it correct P2TH address'''

    pa_params = param_query(provider.network)
    raw = provider.getrawtransaction(deck_id, 1)
    vout = raw["vout"][0]["scriptPubKey"].get("addresses")[0]
    error = {"error": "This deck is not properly tagged."}

    if prod:
        assert vout == pa_params.P2TH_addr, error
        return True
    else:
        assert vout == pa_params.test_P2TH_addr, error
        return True

def load_deck_p2th_into_local_node(provider, deck):
    '''
    load deck p2th into local node,
    this allows building of proof-of-timeline for this deck
    '''

    assert isinstance(provider, RpcNode), {"error": "You can load privkeys only into local node."}
    error = {"error": "Deck P2TH import went wrong."}

    provider.importprivkey(deck.p2th_wif, deck.name)
    assert deck.p2th_address in provider.getaddressesbyaccount(deck.name), error

def validate_card_transfer_p2th(provider, txid, deck):
    '''validate if card_transfer transaction pays to deck p2th in vout[0]'''

    raw = provider.getrawtransaction(txid, 1)
    error = {"error": "Card transfer is not properly tagged."}

    assert raw["vout"][0]["scriptPubKey"].get("addresses")[0] == deck.p2th_address, error

def parse_card_transfer_metainfo(protobuf):
    '''decode card_spawn tx op_return protobuf message and validate it.'''

    card = paproto.CardTransfer()
    card.ParseFromString(protobuf)

    assert card.version > 0, {"error": "Card metainfo incomplete, version can't be 0."}

    return {
        "version": card.version,
        "number_of_decimals": card.number_of_decimals,
        "amount": card.amounts,
        "asset_specific_data": card.asset_specific_data
    }

def amount_to_exponent(amount, number_of_decimals):
    '''encode amount integer as exponent'''

    return int(amount * 10**number_of_decimals)

def exponent_to_amount(exponent, number_of_decimals):
    '''exponent to integer to be written on the chain'''

    return exponent / 10**number_of_decimals

