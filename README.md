# pypeerassets

Official Python implementation of the PeerAssets protocol.

This library aims to implement the asset protocol itself, but also provide elementary interfaces with the underlying blockchain.
Once completed library should be able to spawn asset decks, deduce proof-of-timeline for each deck and handle all asset transactions
while not depending on local blockchain node until it needs to broadcast the transaction or fetch group of transactions.
Furthermore, library will aim to cover the needs of DAC or DAC-like projects using the PeerAssets protocol.

Library is coded with Python3 in mind, compatibility with older python releases is not in our scope.

### Dependencies

`pip install --user secp256k1 base58`

### Clone

`https://github.com/PeerAssets/pypeerassets`

## How to use it:

(so far only Kutil is implemented)

`from pypeerassets import Kutil`

`mykey = Kutil(network=ppc)`

`mykey = Kutil(wif=wif)` # Import privkey from wallet.

`mykey.address`

`mykey.to_wif()`
