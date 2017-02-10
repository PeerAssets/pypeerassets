import unittest
from hashlib import sha256
from pypeerassets.kutil import Kutil

class KutilTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('''Starting Kutil class tests.
                This class handles all things cryptography.''')

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

    def test_key_generation_from_seed(self):
        '''check if key generation is what is expected from seed'''

        seed = "Hello PeerAssets."
        mykey = Kutil(seed=seed)

        self.assertEqual(mykey.privkey, '680510f7f5e622347bc8d9e54e109a9192353693ef61d82d2d5bdf4bc9fd638b')
        self.assertEqual(mykey.pubkey, '037cf9e7664b5d10ce209cf9e2c7f68baa06f1950114f25677531b959edd7e670c')

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

    def test_sign_message(self):
        '''test Bitcoin style signature'''

        WIF = "cVzLwfaC59g5CQuM1qCHiYTeWNWpHPuPGpnoXciV7Mv3vjgp8vZx"
        string = "hello world."
        signature = "IAO8Yt7+tVD2XEB7b6lI78c+TVeDCFhSAqgbIKVjnHW3vpOz/zkkBs/ZxlfQW/IIZK/9ZrpIQmmMiQ9MLKY83NU="

        mykey = Kutil(wif=WIF)
        self.assertEqual(mykey.sign_message(string), signature)

if __name__ == '__main__':
    unittest.main()
