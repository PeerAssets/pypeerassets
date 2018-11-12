# Example of Once Issue Mode.

# Suppose Alice, Bob and Charles are forming a new company: Friendly Co.

# Alice provides 50% of the initial capital, Bob 25% and Charles 25%.

# To keep track of their new venture, Alice decides to spawn a PeerAssets Deck
# for Friendly Co. with 1,000,000 Cards to split between the founders (500,000
# for Alice, 250,000 for Bob and 250,000 for Charles).

# Additionally, by using the Once Issue Mode on the PeerAssets Deck Alice is
# guaranteeing that only 1,000,000 of the Friendly Co. Cards will ever exist.


import time

import pypeerassets as pa
from pypeerassets.protocol import IssueMode
from pypeerassets.provider import RpcNode
from pypeerassets.transactions import sign_transaction


# Setup:

# Install the Peercoin Wallet software and make the testnet rpc server
# available. A peercoin.conf with the following options should work:
#
# testnet=1
# server=1
# txindex=1
# rpcuser=<rpc username>
# rpcpassword=<rpc password>

RPC_USERNAME = "<rpc username>"
RPC_PASSWORD = "<rpc password>"

# Generate an address for Friendly Co., Alice, Bob and Charles using the
# Peercoin Wallet software:

FRIENDLY_CO = "<testnet address>"
ALICE = "<testnet address>"
BOB = "<testnet address>"
CHARLES = "<testnet address>"

# Obtain testnet coins for Friendly Co. and Alice
# using https://faucet.peercoinexplorer.net

# Run the script `python once_issue_mode_example.py` :)


def wait_for_confirmation(provider, transaction_id):
    'Sleep on a loop until we see a confirmation of the transaction.'
    while(True):
        transaction = provider.gettransaction(transaction_id)
        if transaction["confirmations"] > 0:
            break
        time.sleep(10)


if __name__ == "__main__":

    # Deck Spawn

    print("Build, sign and send the Friendly Co. Deck spawning transaction...")

    rpc_node = RpcNode(testnet=True, username=RPC_USERNAME, password=RPC_PASSWORD)

    friendly_co_key = pa.Kutil(
        network="tppc",
        from_wif=rpc_node.dumpprivkey(FRIENDLY_CO),
    )

    deck = pa.Deck(
        name="Friendly Co. Deck",
        number_of_decimals=0,
        issue_mode=IssueMode.ONCE.value,
        network="tppc",
        production=False,
        version=1,
        issuer=FRIENDLY_CO,
    )

    deck_spawn_tx = pa.deck_spawn(
        provider=rpc_node,
        deck=deck,
        inputs=rpc_node.select_inputs(FRIENDLY_CO, 0.02),
        change_address=FRIENDLY_CO,
    )
    deck_spawn_tx = sign_transaction(rpc_node, deck_spawn_tx, friendly_co_key)
    rpc_node.sendrawtransaction(deck_spawn_tx.hexlify())

    print("Transaction to create the Friendly Co. Deck sent to the network!")
    print("Transaction ID: " + deck_spawn_tx.txid)
    print("Waiting for confirmation...")
    wait_for_confirmation(rpc_node, deck_spawn_tx.txid)
    print("Friendly Co. Deck created!")
    deck.id = deck_spawn_tx.txid
    print("Deck ID: " + deck.id)
    print("Deck P2TH Address: " + deck.p2th_address)

    print("Double checking that the Friendly Co. Deck exists...")
    found_deck = pa.find_deck(
        provider=rpc_node,
        key=deck.id,
        version=1,
        prod=False,
    )
    assert found_deck is not None, "Should have found the Friendly Co. Deck."
    print("Found the Friendly Co. Deck!")

    # Card Issue

    print("Build, sign and send the Card Issue transaction to Alice...")

    card_transfer = pa.CardTransfer(
        deck=deck,
        receiver=[ALICE],
        amount=[1000000],
        sender=FRIENDLY_CO,
    )

    card_transfer_tx = pa.card_transfer(
        provider=rpc_node,
        card=card_transfer,
        inputs=rpc_node.select_inputs(FRIENDLY_CO, 0.02),
        change_address=FRIENDLY_CO,
    )
    card_transfer_tx = sign_transaction(rpc_node, card_transfer_tx, friendly_co_key)
    rpc_node.sendrawtransaction(card_transfer_tx.hexlify())

    print("Transaction to issue Friendly Co. Cards sent to the network!")
    print("Transaction ID: " + card_transfer_tx.txid)
    print("Waiting for confirmation...")
    wait_for_confirmation(rpc_node, card_transfer_tx.txid)
    print("Friendly Co. Cards created!")

    print("Double checking the Friendly Co. Deck State...")
    cards = pa.find_all_valid_cards(rpc_node, deck)
    deck_state = pa.DeckState(cards)
    assert len(deck_state.balances) == 1, "Only Alice should have Friendly Co. Cards."
    assert deck_state.balances[ALICE] == 1000000, "Alice should have the initial 1,000,000 Cards."
    print("Friendly Co. Deck State looks good!")

    # Card Transfer

    print("Build, sign and send the Card Transfer transaction to Bob and Charles...")

    alice_key = pa.Kutil(
        network="tppc",
        from_wif=rpc_node.dumpprivkey(ALICE),
    )

    card_transfer = pa.CardTransfer(
        deck=deck,
        receiver=[BOB, CHARLES],
        amount=[250000, 250000],
        sender=ALICE,
    )

    card_transfer_tx = pa.card_transfer(
        provider=rpc_node,
        card=card_transfer,
        inputs=rpc_node.select_inputs(ALICE, 0.02),
        change_address=ALICE,
    )
    card_transfer_tx = sign_transaction(rpc_node, card_transfer_tx, alice_key)
    rpc_node.sendrawtransaction(card_transfer_tx.hexlify())

    print("Transaction to transfer Friendly Co. Cards sent to the network!")
    print("Transaction ID: " + card_transfer_tx.txid)
    print("Waiting for confirmation...")
    wait_for_confirmation(rpc_node, card_transfer_tx.txid)
    print("Friendly Co. Cards transfered!")

    print("Double checking the Friendly Co. Deck State...")
    cards = pa.find_all_valid_cards(rpc_node, deck)
    deck_state = pa.DeckState(cards)
    assert len(deck_state.balances) == 3, "Alice, Bob and Charles should have Friendly Co. Cards."
    assert deck_state.balances[ALICE] == 500000, "Alice should have 500,000 Cards."
    assert deck_state.balances[BOB] == 250000, "Bob should have 250,000 Cards."
    assert deck_state.balances[CHARLES] == 250000, "Charles should have 250,000 Cards."
    print("Friendly Co. Deck State looks good!")
