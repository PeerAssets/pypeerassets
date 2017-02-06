
'''miscellaneous utilities.'''

import binascii
from pypeerassets.provider import RpcNode, Mintr
from pypeerassets.constants import *
from pypeerassets import paproto

def localnode_testnet_or_mainnet(node):
    '''check if local node is configured to testnet or mainnet'''

    if node.getinfo()["testnet"] is True:
        return "testnet"
    else:
        return "mainnet"

def load_p2th_privkeys_into_node(provider, prod=True):
    '''load production p2th privkey into local node'''

    assert isinstance(provider, RpcNode), {"error": "You can load privkeys only into local node."}
    error = {"error": "Loading P2TH privkey failed."}

    if provider.is_testnet:

        if prod is True:
            provider.importprivkey(testnet_PAPROD, "PAPROD")
            assert testnet_PAPROD_addr in provider.getaddressesbyaccount("PAPROD"), error

        else:
            provider.importprivkey(testnet_PATEST, "PATEST")
            assert testnet_PATEST_addr in provider.getaddressesbyaccount("PATEST"), error

    else:
        if prod is True:
            provider.importprivkey(mainnet_PAPROD, "PAPROD")
            assert mainnet_PAPROD_addr in provider.getaddressesbyaccount("PAPROD"), error

        else:
            provider.importprivkey(mainnet_PAPROD, "PAPROD")
            assert mainnet_PAPROD_addr in provider.getaddressesbyaccount("PAPROD"), error

def find_tx_sender(provider, txid):

    vin = provider.getrawtransaction(txid, 1)["vin"][0]["txid"]
    return provider.getrawtransaction(vin, 1)["vout"][-1]["scriptPubKey"]["addresses"][0]

def find_deck_spawns(provider, prod=True):
    '''find deck spawn transactions via provider,
    it requires that Deck spawn P2TH were imported in local node or
    that remote API knows about P2TH address.'''

    if isinstance(provider, RpcNode):

        if prod:
            decks = [i["txid"] for i in provider.listtransactions("PAPROD")]
        else:
            decks = [i["txid"] for i in provider.listtransactions("PATEST")]

        return decks

    if isinstance(provider, Mintr):

        if prod:
            decks = [i["txid"] for i in provider.listtransactions(mainnet_PAPROD_addr)]
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

def validate_deckspawn_p2th(provider, deck_id, testnet=False, prod=True):
    '''validate if deck spawn pays to p2th in vout[0] and if it correct P2TH address'''

    raw = provider.getrawtransaction(deck_id, 1)
    vout = raw["vout"][0]["scriptPubKey"].get("addresses")[0]
    error = {"error": "This deck is not properly tagged."}

    if testnet:

        if not prod: # if test P2TH
            assert vout == testnet_PATEST_addr, error
            return True
        else:
            assert vout == testnet_PAPROD_addr, error
            return True

    else:

        if not prod: # if test P2TH
            assert vout == mainnet_PATEST_addr, error
            return True
        else:
            assert vout == mainnet_PAPROD_addr, error
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

