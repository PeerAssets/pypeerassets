# pypeerassets

Official Python implementation of the PeerAssets protocol.

This library aims to implement the PeerAssets protocol itself, but also provide elementary interfaces with the underlying blockchain.
Once completed library should be able to spawn asset decks, deduce proof-of-timeline for each deck and handle all asset transactions
while not depending on local blockchain node until it needs to broadcast the transaction or fetch group of transactions.
Furthermore, library will aim to cover the needs of DAC or DAC-like projects using the PeerAssets protocol.

Library is coded with Python3 in mind, compatibility with older Python releases is not in our scope.

### Dependencies

`pip install --user protobuf`

### Clone

`https://github.com/PeerAssets/pypeerassets`

### VirtualEnv Development

There are some snags to setting up a python virtualenv in the typical fashion at the moment.

However, if you manage to locally install `btcpy` you can comment it out in the `requirements.txt` file and then `pip install -r requirements.txt` and `pip install -r requirements-dev.txt` cleanly. Then you can type `pytest` to get the tests to run <3

They're failing at the moment but we'll address that soon :)
