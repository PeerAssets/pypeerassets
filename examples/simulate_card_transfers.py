'''
Crude script which simulates PeerAssets card exchange by
1) generating a number of random keypairs
2) fund the random addresses,
3) send out random card_transfers from random keypairs 

use to populate card_tranfers on the deck and test functionality.
'''

MAX_TRANSACTIONS = 3200
MAX_RECEIVERS = 826
MAX_TRANFERS = 3600
MAX_BURNS = 800

import pypeerassets as pa
from binascii import hexlify
import random
import datetime, time
import pickle
import logging

logging.basicConfig(filename='pypa.log',level=logging.INFO)
logging.info("Started new session: {0}".format(datetime.datetime.now().isoformat()))

provider = pa.RpcNode(testnet=True)
deck = pa.find_deck(provider, "clementines")[0]
change_addr = deck.issuer

try: # try to load keypairs from the file
    keypairs = pickle.load(open("keypairs.db", "rb"))
except:
    keys = [pa.Kutil(network="tppc") for i in range(MAX_RECEIVERS)]
    keypairs = {k.address:v.wif for k, v in zip(keys, keys)}

class Session:
    pass

def total_issuance():
    return len([ct for ct in pa.find_card_transfers(provider, deck) if ct.type is "CardIssue"])

def total_tranfers():
    return len([ct for ct in pa.find_card_transfers(provider, deck) if ct.type is "CardTransfer"])

def total_burns():
    return len([ct for ct in pa.find_card_transfers(provider, deck) if ct.type is "CardBurn"])

def send_to_address(address, amount=0.06):
    '''fund ppc address'''
    print("Address has no funds assigned to...")
    print("Sending funds to: {0}".format(address), "\n")
    logging.info("Sending funds to address: {0}".format(address))
    try:
        provider.sendtoaddress(address, amount)
    except ValueError:
        return

def select_random_address():
    '''select random address to receive cards from keypairs to send to.'''
    l = list(keypairs.keys())
    random.shuffle(l)
    return random.choice(l)

def select_random_keypairs():
    '''select several random addresses'''
    l = list(keypairs.keys())
    random.shuffle(l)
    rand = random.randint(1, 12)
    return random.sample(l, rand)

def c_issue():
    '''issue cards to selected list of random recipients'''

    utxo = provider.select_inputs(0.02, deck.issuer)
    # load random keysets
    receiver = select_random_keypairs()
    # amounts for the receiver
    amount = [round(random.uniform(0.1, 150000),
                     deck.number_of_decimals) for i in range(len(receiver))]

    issue = pa.CardTransfer(deck, receiver, amount) # CardTransfer instance
    raw_issue = hexlify(pa.card_issue(deck, issue, utxo, change_addr)).decode()

    signed = provider.signrawtransaction(raw_issue)
    logging.info("Issue: {0}".format(datetime.datetime.now().isoformat()))
    print("Issuing cards to: {0}".format(receiver))
    txid = provider.sendrawtransaction(signed["hex"])
    logging.info("Issuing cards to: {0} in tx: {1}".format(receiver, txid))
    print(txid)
    Session.total_issuance =+ 1

def c_transfer():
    '''simulate p2p card_transfer'''
    print("Card burn.")

    addr = select_random_address()
    print("Selected addr: {addr}".format(addr=addr))
    if not provider.validateaddress(addr)["ismine"]:
        provider.importprivkey(keypairs[addr])
        print("Imported {address} to wallet.".format(address=addr))
    if provider.getreceivedbyaddress(addr) == 0:
        send_to_address(addr)
        return ## return until the next time
    else:
        try:
            utxo = provider.select_inputs(0.02, addr)
        except Exception as e:
            print("Something went wrong with UTXO selection:", e)
            return

    receiver = select_random_keypairs()
    amount = [round(random.uniform(0.1, 160000), deck.number_of_decimals) for i in range(len(receiver))]
    ct = pa.CardTransfer(deck, receiver, amount) # CardTransfer instance
    raw = hexlify(pa.card_transfer(deck, ct, utxo, change_addr)).decode()
    signed = provider.signrawtransaction(raw)
    print("Sending cards to: {0}".format(receiver))
    logging.info("Transfer: {0}".format(datetime.datetime.now().isoformat()))
    logging.info("Sending cards to: {0}".format(receiver))
    txid = provider.sendrawtransaction(signed["hex"]) # send the tx
    print(txid)
    Session.total_issuance =+ 1

def c_burn():
    '''simulate card burning'''
    print("Card burn.")

    addr = select_random_address()
    if not provider.validateaddress(addr)["ismine"]:
        provider.importprivkey(keypairs[addr])
        print("Imported {address} to wallet.".format(address=addr))
    if provider.getreceivedbyaddress(addr) == 0:
        send_to_address(addr)
        return ## return until the next time
    else:
        try:
            utxo = provider.select_inputs(0.02, addr)
        except Exception as e:
            print("Something went wrong with UTXO selection:", e)
            return

    receiver = [deck.issuer]
    amount = [round(random.randint(1, 40000), deck.number_of_decimals)]
    ct = pa.CardTransfer(deck, receiver, amount)
    raw = hexlify(pa.card_burn(deck, ct, utxo, change_addr)).decode()
    signed = provider.signrawtransaction(raw)
    print("Burning cards from: {0}".format(addr))
    logging.info("Burn: {0}".format(datetime.datetime.now().isoformat()))
    logging.info("Burning cards from: {0}".format(addr))
    txid = provider.sendrawtransaction(signed["hex"]) # send the tx
    print(txid)
    Session.total_burns =+ 1

#######################################################################

Session.total_issuance = total_issuance()
print(Session.total_issuance)
Session.total_burns = total_burns()
print(Session.total_burns)
Session.total_transfers = total_tranfers()
print(Session.total_transfers)

while Session.total_issuance + Session.total_burns + Session.total_transfers < MAX_TRANSACTIONS:
    
    print("Total issuances: " , Session.total_issuance)
    if not Session.total_issuance > MAX_RECEIVERS:
        c_issue()
        time.sleep(random.randint(120, 560))

    print("Total transfers: ", Session.total_transfers)
    if not Session.total_transfers > MAX_TRANFERS:
        c_transfer()
        t = random.randint(1, 360)
        print("Will sleep for: {0} seconds.".format(t))
        time.sleep(t)

    print("Total burns: ", Session.total_burns)
    if not Session.total_burns > MAX_BURNS:
        c_burn()
        t = random.randint(1, 360)
        print("Will sleep for: {0} seconds.".format(t))
        time.sleep(t)

## when done write keypairs to file
with open('keypairs.db', 'wb') as outfile:
    pickle.dump(keypairs, outfile)

