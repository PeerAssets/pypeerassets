from pypeerassets.providers.node import RpcNode
from pypeerassets.transactions import *

provider = RpcNode(testnet=True)

inputs = provider.select_inputs(0.1)
outputs = [{'redeem': 1,'outputScript': monosig_script("mvASQQirJsYTTVwd1zNqnYmRWUV53ZurT4")}]

raw = make_raw_transaction(inputs, outputs)