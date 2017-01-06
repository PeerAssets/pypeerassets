import unittest
from pypeerassets.peerassets import parse_deckspawn_metainfo

class PeerAssetsTestCase(unittest.TestCase):
    '''tests for protobuf manipulation'''

    def test_parse_deckspawn_metainfo(self):
        '''tests if loading of deck parameteres from protobuf'''

        string = b'\x08\x01\x12\x0cmy_test_deck\x18\x03 \x02'

        self.assertEqual(parse_deckspawn_metainfo(string), {'issue_mode': 2,
                                                            'name': 'my_test_deck',
                                                            'number_of_decimals': 3,
                                                            'version': 1})
        #incomplete_string = b'\x08\x01\x12\x03ttt'


if __name__ == '__main__':
    unittest.main()