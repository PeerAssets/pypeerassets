from transactions import *
import paproto

version = 1

def deck_spawn(short_name, number_of_decimals, issue_mode, asset_specific_data=None):

    assert ds_validate(issue_mode), 'Invalid Issue Mode'

    deck = paproto.DeckSpawn()
    deck.version = version
    deck.short_name = short_name
    deck.number_of_decimals = number_of_decimals
    deck.issue_mode = issue_mode

    if asset_specific_data is not None:
        deck.asset_specific_data = asset_specific_data

    return deck.SerializeToString()

def card_transfer(amount, number_of_decimals, asset_specific_data=None):

    card = paproto.CardTransfer()
    card.version = version
    card.number_of_decimals = number_of_decimals

    if asset_specific_data is not None:
        card.asset_specific_data = asset_specific_data

    return card.SerializeToString()

def ds_validate(issue_mode):
    return issue_mode in paproto.DeckSpawn().MODE.values()


def vouts(address,data):
    ''' Returns a list containing the order in which P2TH and OP_RETURN vouts
        are to be structured per the Protocol specifications'''

    output = []
    output.append({'redeem':10000,'outputScript': monosig_script(address)}) # P2TH 1000000
    output.append({'redeem':0,'outputScript': op_return_script(data)}) # data per protocol specifications
    return output