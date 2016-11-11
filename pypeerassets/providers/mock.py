
'''Mock provider, with usable but fake data, used for testing'''

def select_inputs(amount):
    '''returns list of UTXO's'''

    # inputs expected as [{'txid':txhash,'vout':index,'scriptSig':txinScript},..]

    return [{
        'txid': 'ff6739fefb883a6db24efa20d6440f65082cc0557d5f7f21d1a31afaa267ee67',
        'vout': 1,
        'scriptSig': '2102f7552f53d240ba22461351808041d267f941a2fd94e948e5817822459725abdeac'
    },
    {
        'txid': 'fb23ec93649080a848ba746d90c744db2e474797cbb9d3ad2c6aba08d8eff9b7',
        'vout': 2,
        'scriptSig': '210329706d16792f1b7661bb7f35660eb2a6858110dd5259ac84a12aa1838efea86dac'
        }
    ]