'''various protocol contants'''

from collections import namedtuple

Network = namedtuple('Network', [
    'network_name',
    'network_shortname',
    'P2TH_wif',
    'P2TH_addr',
    'test_P2TH_wif',
    'test_P2TH_addr',
    'P2TH_fee',
])

params = (

    ## PPC mainnet
    Network("Peercoin", "ppc", "U624wXL6iT7XZ9qeHsrtPGEiU78V1YxDfwq75Mymd61Ch56w47KE",
            "PAprodbYvZqf4vjhef49aThB9rSZRxXsM6", "UAbxMGQQKmfZCwKXAhUQg3MZNXcnSqG5Z6wAJMLNVUAcyJ5yYxLP",
            "PAtesth4QreCwMzXJjYHBcCVKbC4wjbYKP", float(0.01)),

    ## PPC testnet
    Network("Peercoin-testnet", "tppc", "cTJVuFKuupqVjaQCFLtsJfG8NyEyHZ3vjCdistzitsD2ZapvwYZH",
            "miHhMLaMWubq4Wx6SdTEqZcUHEGp8RKMZt", "cQToBYwzrB3yHr8h7PchBobM3zbrdGKj2LtXqg7NQLuxsHeKJtRL",
            "mvfR2sSxAfmDaGgPcmdsTwPqzS6R9nM5Bo", float(0.01))
)

def param_query(query):
    '''find matching parameter among the networks'''

    for network in params:
        for field in network:
            if field == query:
                return network

