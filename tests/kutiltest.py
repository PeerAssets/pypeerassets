import unittest
from pypeerassets.kutil import Kutil

class KutilTestCase(unittest.TestCase):

    def test_network_parameter_load(self):
        '''tests if loading of network parameteres is accurate'''

        mykey = Kutil(network="ppc")

        self.assertEqual(mykey.denomination, 1000000)
        self.assertEqual(mykey.wif_prefix, b'b7')
        self.assertEqual(mykey.pubkeyhash, b'37')

    def test_key_generation(self):
        '''test privkey/pubkey generation'''

        mykey = Kutil(network="ppc")

        # check if keys are in proper format
        self.assertTrue(isinstance(mykey.keypair.private_key, bytes))
        self.assertTrue(isinstance(mykey.keypair.pubkey.serialize(), bytes))

        # check if key generation is what is expected from seed
        '''
        self.assertEqual(mykey.privkey, '416b2b925a4b004a3ccb92295e5a835cfd854ef7c4afde0b0eabd5d2492594e2')
        self.assertEqual(mykey.pubkey, '03d612848fca55fd57760ff204434d41091927eeda4dfec39e78956b2cc6dbd62b')
        '''

    def test_address_generation(self):
        '''test if addresses are properly made'''

        mykey = Kutil(network="ppc")

        self.assertTrue(mykey.address.startswith("P"))
        self.assertTrue(isinstance(mykey.address, str))
        self.assertTrue(len(mykey.address), 34)

    def test_wif_import(self):
        '''test improting WIF privkey'''

        mykey = Kutil(wif="7A6cFXZSZnNUzutCMcuE1hyqDPtysH2LrSA9i5sqP2BPCLrAvZM")

        self.assertEqual(mykey.address, 'PJxwxuBqjpHhhdpV6KY1pXxUSUNb6omyNW')
        self.assertEqual(mykey.pubkey, '02a119079ef5be1032bed61cc295cdccde58bf70e0dd982399c024d1263740f398')
        self.assertEqual(mykey.privkey, 'b43d38cdfa04ecea88f7d9d7e95b15b476e4a6c3f551ae7b45344831c3098da2')

if __name__ == '__main__':
    unittest.main()
