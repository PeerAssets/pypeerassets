import unittest
from pypeerassets.pautils import *
from pypeerassets import RpcNode, Mintr

class PAutilsTestCase(unittest.TestCase):
    '''tests various PeerAssets utility functions.'''

    @classmethod
    def setUpClass(cls):
        print('''Starting tests for various PeerAssets utility functions...''')

    def test_parse_deckspawn_metainfo(self):
        '''tests if loading of deck parameteres from protobuf works as it should.'''

        string = b'\x08\x01\x12\x0cmy_test_deck\x18\x03 \x02'
        self.assertEqual(parse_deckspawn_metainfo(string), {'issue_mode': "ONCE",
                                                            'name': 'my_test_deck',
                                                            'number_of_decimals': 3,
                                                            'version': 1,
                                                            'asset_specific_data': b''})

        string = b'\x12\x06faulty\x18\x01' # without version and issue mode
        self.assertRaises(AssertionError, parse_deckspawn_metainfo, string)

        string = b'\x08\x01\x18\x05 \x04' # without deck name
        self.assertRaises(AssertionError, parse_deckspawn_metainfo, string)

    def test_validate_deckspawn_p2th(self):
        '''test deckspawn p2th validation'''

        node = RpcNode(testnet=True)

        self.assertTrue(validate_deckspawn_p2th(node, "93dff38d65ef25ff9539ea2fa1fda45eb29d8bb989ca91399218c7e83e6630ea",
                                                testnet=True))

        self.assertRaises(AssertionError, validate_deckspawn_p2th, node,
                          "93dff38d65ef25ff9539ea2fa1fda45eb29d8bb989ca91399218c7e83e6630ea",
                          testnet=True, prod_or_test="test")

    """
    def test_read_tx_opreturn(self):
        '''test if it parses the OP_RETURN from tx correctly'''

        node = Mintr()
        self.assertEqual(read_tx_opreturn(node, "2d101a202de7b468a43649bd6eda9dcd6372ba368e829c1e0e5f62640c0bee04"))
    """

if __name__ == '__main__':
    unittest.main()