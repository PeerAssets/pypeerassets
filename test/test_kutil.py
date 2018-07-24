import pytest
from os import urandom
from decimal import Decimal
import time

from btcpy.structs.transaction import Locktime
from btcpy.structs.sig import P2pkhSolver

from pypeerassets.btcpy_peercoin import PeercoinMutableTx, PeercoinTx
from pypeerassets.kutil import Kutil
from pypeerassets.provider import Explorer
from pypeerassets.networks import net_query
from pypeerassets.transactions import tx_output, find_parent_outputs, p2pkh_script


def test_key_generation():
    '''test privkey/pubkey generation.'''

    mykey = Kutil(network="ppc")

    assert isinstance(mykey.privkey, str)
    assert isinstance(mykey.pubkey, str)


def test_key_generation_from_seed():
    '''check if key generation is what is expected from seed.'''

    seed = "Hello PeerAssets."
    mykey = Kutil(from_string=seed, network="tppc")

    assert mykey.privkey == '680510f7f5e622347bc8d9e54e109a9192353693ef61d82d2d5bdf4bc9fd638b'
    assert mykey.pubkey == '037cf9e7664b5d10ce209cf9e2c7f68baa06f1950114f25677531b959edd7e670c'


def test_address_generation():
    '''test if addresses are properly made'''

    privkey = bytearray(urandom(32))

    assert Kutil(network="ppc", privkey=privkey).address.startswith("P")

    assert isinstance(Kutil(network='ppc').address, str)
    assert len(Kutil(network='ppc').address) == 34


def test_mainnet_wif_import():
    '''test importing WIF privkey'''

    mykey = Kutil(network='ppc', from_wif="U624wXL6iT7XZ9qeHsrtPGEiU78V1YxDfwq75Mymd61Ch56w47KE")

    assert mykey.address == 'PAprodbYvZqf4vjhef49aThB9rSZRxXsM6'
    assert mykey.pubkey == '023aaca6c4f022543f4a2920f66544a6ce89746f7fce4da35d63b5886fdac06634'
    assert mykey.privkey == '1b19749afd007bf6db0029e0273a46409bc160b9349031752bbc3cd913bbbdd3'


def test_wif_export():
    '''test Kutil WIF export'''

    mykey = Kutil(network='ppc',
                  privkey=bytearray.fromhex('1b19749afd007bf6db0029e0273a46409bc160b9349031752bbc3cd913bbbdd3')
                 )

    assert isinstance(mykey.wif, str)
    assert mykey.wif == 'U624wXL6iT7XZ9qeHsrtPGEiU78V1YxDfwq75Mymd61Ch56w47KE'


def test_sign_transaction():

    network_params = net_query('tppc')
    provider = Explorer(network='tppc')
    key = Kutil(network='tppc',
                privkey=bytearray.fromhex('9e321f5379c2d1c4327c12227e1226a7c2e08342d88431dcbb0063e1e715a36c')
                )
    dest_address = 'mwn75Gavp6Y1tJxca53HeCj5zzERqWagr6'

    unspent = provider.select_inputs(key.address, 0.63)  # 0.69
    output = tx_output(network='tppc',
                       value=Decimal(0.1),
                       n=0, script=p2pkh_script(network='tppc',
                                                address=dest_address)
                       )

    unsigned = PeercoinMutableTx(version=1,
                                 timestamp=int(time.time()),
                                 ins=unspent['utxos'],
                                 outs=[output],
                                 network=network_params,
                                 locktime=Locktime(0)
                                 )

    parent_outputs = [find_parent_outputs(provider, i) for i in unsigned.ins]
    solver = P2pkhSolver(key._private_key)

    signed = unsigned.spend(parent_outputs,
                            [solver for i in parent_outputs])

    assert isinstance(signed, PeercoinTx)
