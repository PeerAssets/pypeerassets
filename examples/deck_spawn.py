'''
Spawn new PeerAssets deck on Peercoin testnet using local testnet node.
'''

import pypeerassets as pa
from binascii import hexlify

provider = pa.RpcNode(testnet=True)

utxo = provider.select_inputs(0.02) ## we need 0.02 PPC
change_addr = "mwkFUPUrh6LsXyMvBY2mz6btiJjuTxGgT8" 

new_deck = pa.Deck("my_new_testnet_deck", number_of_decimals=2, issue_mode="MULTI", asset_specific_data="hello world.", network="tppc")

raw_tx = hexlify(pa.deck_spawn(new_deck, utxo, change_addr)).decode()

signed = provider.signrawtransaction(raw_tx)

provider.sendrawtransaction(signed["hex"]) # send the tx

'''
Now wait for the tx confirm (1) and visit http://137.74.40.81:4000/ to see your assets listed.
'''