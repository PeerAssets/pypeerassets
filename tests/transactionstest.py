import unittest
from binascii import unhexlify
from pypeerassets.transactions import *

class TransactionsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('''Starting transactions, verify if transaction assembly/dissasembly is working as it should.''')

    def test_get_hash_160(self):

        address = "PUsvrXxav7ryMawmxZk9ShmGiuCJWjdPmo"
        self.assertEqual(get_hash160(address), b'\xde\x8d\xa6A3P\x18\x8b\x95H\x8d\xb2\xf9\tmu\xb6U\xfc\xc7')

    def test_transaction_dissasembly_test(self):
        '''verifies that transaction dissasembly is in order'''

        tx = "10060b0349d3c84a7d88bd396a703d6df39c587bf8169fef73db46e7b346efe5"
        ## getrawtx by ppcoind
        rawtx = "0100000055842d5801893e129cc07ed2799eef39c3961baec2ce58e273ce51ae9f16fd92be9924bbf5020000004a493046022100b4de95eb9652b86fe3070ab9c1ccf60ec700638848589416f48bfaa0342c2d46022100ed7ff3ec83324c146e3ce8123854a62a9953f6ebd027b77330a1c2b9f0a5847501ffffffff020000000000000000007096050d000000002321027f2101a1eb0ef4f53ab48919a0f390dfcaddd6b8104324b4ef8d2654b08b3722ac00000000"

        ## decoded by ppcoind
        decoded_raw_tx = {
            'vout': [
                {'scriptPubKey': '', 'value': 0.0},
                {'scriptPubKey': '21027f2101a1eb0ef4f53ab48919a0f390dfcaddd6b8104324b4ef8d2654b08b3722ac',
                 'value': 218.47}
            ],
            'timestamp': 1479378005,
            'version': 1,
            'vin': [
                {
                    'vout': 2,
                    'sequence': 4294967295,
                    'scriptSig': '493046022100b4de95eb9652b86fe3070ab9c1ccf60ec700638848589416f48bfaa0342c2d46022100ed7ff3ec83324c146e3ce8123854a62a9953f6ebd027b77330a1c2b9f0a5847501',
                    'txid': 'f5bb2499be92fd169fae51ce73e258cec2ae1b96c339ef9e79d27ec09c123e89'
                }
            ],
            'locktime': 0
        }

        self.assertEqual(unpack_raw_transaction(unhexlify(rawtx)), decoded_raw_tx)

if __name__ == '__main__':
    unittest.main()
