'''
Crude script which simulates PeerAssets card exchange by
1) generating a number of random keypairs
2) fund the random addresses,
3) send out random card_transfers from random keypairs 

use to populate card_tranfers on the deck and test functionality.
'''

MAX_TRANSACTIONS = 3000
MAX_RECEIVERS = 800
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

def total_issuance():
    return len([ct for ct in pa.find_all_card_transfers(provider, deck) if ct.type is "CardIssue"])

def total_tranfers():
    return len([ct for ct in pa.find_all_card_transfers(provider, deck) if ct.type is "CardTransfer"])

def total_burns():
    return len([ct for ct in pa.find_all_card_transfers(provider, deck) if ct.type is "CardBurn"])

def send_to_address(address, amount=0.04):
    '''fund ppc address'''
    print("Address has no funds assigned to...")
    print("Sending fund to: {0}".format(address))
    logging.info("Sending funds to address: {0}".format(address))
    provider.sendtoaddress(address, amount)

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
    receivers = select_random_keypairs()
    # amounts for the receivers
    amounts = [round(random.uniform(0.1, 150000),
                     deck.number_of_decimals) for i in range(len(receivers))]

    issue = pa.CardTransfer(deck, receivers, amounts) # CardTransfer instance
    raw_issue = hexlify(pa.card_issue(deck, issue, utxo, change_addr)).decode()

    signed = provider.signrawtransaction(raw_issue)
    logging.info("Issue: {0}".format(datetime.datetime.now().isoformat()))
    print("Issuing cards to: {0}".format(receivers))
    logging.info("Issuing cards to: {0}".format(receivers))
    txid = provider.sendrawtransaction(signed["hex"])
    print(txid)

def c_transfer():
    '''simulate p2p card_transfer'''

    addr = select_random_address()
    if not provider.validateaddress(addr)["ismine"]:
        provider.importprivkey(keypairs[addr])
    if provider.getreceivedbyaddress(addr) == 0.0:
        send_to_address(addr)
        return ## return until the next time
    else:
        try:
            utxo = provider.select_inputs(0.02, addr)
        except ValueError:
            return

    receivers = select_random_keypairs()
    amounts = [round(random.uniform(0.1, 100000), deck.number_of_decimals) for i in range(len(receivers))]
    ct = pa.CardTransfer(deck, receivers, amounts) # CardTransfer instance
    raw = hexlify(pa.card_transfer(deck, ct, utxo, change_addr)).decode()
    signed = provider.signrawtransaction(raw)
    print("Sending cards to: {0}".format(receivers))
    logging.info("Transfer: {0}".format(datetime.datetime.now().isoformat()))
    logging.info("Sending cards to: {0}".format(receivers))
    txid = provider.sendrawtransaction(signed["hex"]) # send the tx
    print(txid)

def c_burn():
    '''simulate card burning'''

    addr = select_random_address()
    if not provider.validateaddress(addr)["ismine"]:
        provider.importprivkey(keypairs[addr])
    if provider.getreceivedbyaddress(addr) == 0.0:
        send_to_address(addr)
        return ## return until the next time
    else:
        try:
            utxo = provider.select_inputs(0.02, addr)
        except ValueError:
            return

    utxo = provider.select_inputs(0.02)
    receivers = [deck.issuer]
    amounts = [round(random.randint(1, 160000), deck.number_of_decimals, deck.number_of_decimals)]
    ct = pa.CardTransfer(deck, receivers, amounts)
    raw = hexlify(pa.card_burn(deck, ct, utxo, change_addr)).decode()
    signed = provider.signrawtransaction(raw)
    print("Burning cards from: {0}".format(addr))
    logging.info("Burn: {0}".format(datetime.datetime.now().isoformat()))
    logging.info("Burning cards from: {0}".format(addr))
    txid = provider.sendrawtransaction(signed["hex"]) # send the tx
    print(txid)

#######################################################################

while total_issuance() + total_burns() + total_tranfers() < MAX_TRANSACTIONS:

    if total_issuance() < MAX_RECEIVERS:
        c_issue()
        time.sleep(random.randint(220, 760))

    if total_tranfers() < MAX_TRANFERS:
        c_transfer()
        time.sleep(random.randint(15, 800))

    if total_burns() < MAX_BURNS:
        c_burn()
        time.sleep(random.randint(120, 720))

## when done write keypairs to file
with open('keypairs.db', 'wb') as outfile:
    pickle.dump(keypairs, outfile)
