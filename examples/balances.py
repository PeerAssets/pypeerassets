"""find <address> card balance on this <deck>"""

import sys
import pypeerassets as pa
from pypeerassets.protocol import validate_card_issue_modes
provider = pa.RpcNode(testnet=True)

print("Searching cards on deck {deck}.".format(deck=sys.argv[1]))
deck = pa.find_deck(provider, sys.argv[1])[0]
cards = [i.__dict__ for i in pa.find_card_transfers(provider, deck)]
my_addr = str(sys.argv[2])  # mkXdyMPX8D7EH7CZcYfQEBvoZhp8MEUgdB


class Balance:

    received = []
    sent = []

    @classmethod
    def balance(cls):
        return sum((i["amount"][0] for i in cls.received)) - sum((i["amount"][0] for i in cls.sent))


# first figure out if cards issued are legit
issues = (i for i in cards if i["type"] == "CardIssue")
issues = list(validate_card_issue_modes(deck, issues))
c = (i for i in cards if i in issues)  # drop invalid issued cards

Balance.received = [i for i in c if i["receiver"][0] == my_addr]
Balance.sent = [i for i in c if i["sender"] == my_addr]

print("Balance of {address} address is {balance}".format(address=my_addr,
                                                 balance=Balance.balance()))

