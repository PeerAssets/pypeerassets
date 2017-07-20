import pytest
from pypeerassets import protocol


def test_deck_object():
    '''test creation of deck objects'''

    deck = protocol.Deck(name="decky", number_of_decimals=2, issue_mode="MULTI",
                         network="ppc", production=True,
                         asset_specific_data="Just testing.")

    assert deck.__dict__ == {'asset_id': None,
                             'asset_specific_data': 'Just testing.',
                             'issue_mode': 'MULTI',
                             'issue_time': None,
                             'issuer': '',
                             'name': 'decky',
                             'network': 'ppc',
                             'number_of_decimals': 2,
                             'production': True,
                             'testnet': False,
                             'version': 1
                             }
