"""find <address> card balance on this <deck>"""

import pypeerassets as pa
from pypeerassets.provider import RpcNode
from pypeerassets.protocol import DeckState

provider = RpcNode(testnet=True)
state = None



def get_state(deck):
    deck = pa.find_deck(provider,deck)[0]
    cards = pa.find_card_transfers(provider,deck)
    return DeckState(cards)

def get_balance(state, address):
    print(state.balances[address])

def get_balances(state):
    print(state.balances)

def get_total(state):
    print(state.total)

def get_checksum(state):
    print(state.checksum)
    
def get_burned(state):
    print(state.burned)
    
while True:
    try:
        deck = input("Deck Identifier: ")
        state = get_state(deck)
        print("**** {} Deck loaded ****".format(deck))
        print("To print all address balances type 'all' in Address input")
        break
    except IndexError:
        print('{"error": "Deck not found, try again"}')
        continue

while True:  
    
    try:
        address = input("Address: ")
        
        if address == 'all':
            get_balances(state)
        else:
            get_balance(state,address)
        continue
    except KeyError:
        print('{"error": "Address not found, try another or subscribe to deck"}')
        continue
    else:
        break

