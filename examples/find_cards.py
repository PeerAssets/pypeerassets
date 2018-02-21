'''
Find card transfers for <deck>.
'''

import sys
import pypeerassets as pa
provider = pa.Cryptoid(network="tppc")

print("Searching for deck {deck}.".format(deck=sys.argv[1]))
deck = pa.find_deck(provider, sys.argv[1])[0]
cards = pa.find_card_transfers(provider, deck)

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("This deck issuer has issued: {cards} cards in {transfers} card issue transactions.".format(
      cards=round(sum((i.amount[0] for i in cards if i.type == "CardIssue")), deck.number_of_decimals),
      transfers=len([i for i in cards if i.type == "CardIssue"])
      ))

print("Peers on this deck have transacted {cards} cards in {transfers} card transactions.".format(
      cards=round(sum((i.amount[0] for i in cards if i.type == "CardTransfer")), deck.number_of_decimals),
      transfers=len([i for i in cards if i.type == "CardTransfer"])
      ))

print("Peers on this deck have burned {cards} cards in {transfers} card transactions.".format(
      cards=round(sum((i.amount[0] for i in cards if i.type == "CardBurn")), deck.number_of_decimals),
      transfers=len([i for i in cards if i.type == "CardBurn"])
     ))

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
