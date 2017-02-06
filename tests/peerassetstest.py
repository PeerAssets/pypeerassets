import unittest
from pypeerassets.main import parse_deckspawn_metainfo
from pypeerassets import Kutil

class PeerAssetsTestCase(unittest.TestCase):
    '''tests for protobuf manipulation'''

    @classmethod
    def setUpClass(cls):
        print('''Starting PeerAssets tests.
                This class handles all things PeerAssets protocol.''')

    def test_parse_deckspawn_metainfo(self):
        '''tests if loading of deck parameteres from protobuf'''

        string = b'\x08\x01\x12\x0cmy_test_deck\x18\x03 \x02'
        self.assertEqual(parse_deckspawn_metainfo(string), {'issue_mode': 2,
                                                            'name': 'my_test_deck',
                                                            'number_of_decimals': 3,
                                                            'version': 1})

    def test_parse_invalid_deckspawn_metainfo(self):
        '''test if it fails on faulty deckspawn metainfo'''

        string = b'\x12\x06faulty\x18\x01' # without version and issue mode
        self.assertRaises(AssertionError, parse_deckspawn_metainfo, string)

        string = b'\x08\x01\x18\x05 \x04' # without deck name
        self.assertRaises(AssertionError, parse_deckspawn_metainfo, string)

        string = b'\x08\x01\x12\x06faulty \x02' # without number_of_decimals
        self.assertRaises(AssertionError, parse_deckspawn_metainfo, string)


class P2THTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('''Starting PeerAssets tests.
                This class handles all things PeerAssets protocol.''')

        cls.txid = "c23375caa1ba3b0eec3a49fff5e008dede0c2761bb31fddd830da32671c17f84"

    def test_p2th_address_generation(self):
        '''generating deck p2th from deck spawn id'''

        key = Kutil(network="ppc", privkey=self.txid)

        self.assertEqual(key.address, "PRoUKDUhA1vgBseJCaGMd9AYXdQcyEjxu9")
        self.assertEqual(key.wif, "UBctiEkfxpU2HkyTbRKjiGHT5socJJwCny6ePfUtzo8Jad9wVzeA")

    def test_testnet_p2th_address_generation(self):
        '''generating testnet deck p2th from deck spawn id'''

        key = Kutil(network="tppc", privkey=self.txid.encode())

        self.assertEqual(key.address, "mxjFTJApv7sjz9T9a4vCnAQbmsqSoL8VWo")
        self.assertEqual(key.wif, "cU6CjGw3mRmirjiUZfRkJ1aj2D493k7uuhywj6tCVbLAMABy4MwU")

if __name__ == '__main__':
    unittest.main()