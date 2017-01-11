import unittest
from pypeerassets.providers.mintr import Mintr

class MintrTestCase(unittest.TestCase):
    '''tests for Mintr provider'''

    @classmethod
    def setUpClass(cls):
        print('''Starting Mintr API wrapper test.''')

    def test_getinfo(self):

        self.assertEqual(Mintr().getinfo(), {"testnet": False})

    def test_getrawtransaction(self):

        tx = {'avgcoindaysdestroyed': '1.033657406',
              'coindaysdestroyed': '17.768570826',
              'fee': '0.01',
              'numvin': '1',
              'numvout': '2',
              'time': '1484062161',
              'tx_hash': '147c4daf47293fb670efd97dd7f9f6e964f515e6478e0cc3a668e4330f12ad6f',
              'valuein': '17.19',
              'valueout': '17.18',
              'vin': [{'address': 'PWbafEjfujD1UhexfrCU5oc3K4kPUrzkun',
                       'avgcoindaysdestroyed': '1.033657406',
                       'coindaysdestroyed': '17.768570826',
                       'value': '17.19'}],
              'vout': [{'address': 'PEmVoMtgFe1WJEXMwhASUfn9UTeupsoGPR', 'value': '16.18'},
                       {'address': 'PPchatrw5hV1y3JUU2kxyL4LQccprbp8FX', 'value': '1'}]}

        self.assertEqual(Mintr().getrawtransaction("147c4daf47293fb670efd97dd7f9f6e964f515e6478e0cc3a668e4330f12ad6f"), tx)

    def test_listtransaction(self):

        self.assertIsInstance(Mintr().listtransactions("PPchatrw5hV1y3JUU2kxyL4LQccprbp8FX"), list)

