
'''miscellaneous utilities.'''

from pypeerassets.constants import mainnet_PAPROD, mainnet_PATEST, testnet_PAPROD, testnet_PATEST

def testnet_or_mainnet(node):
    '''check if local node is configured to testnet or mainnet'''

    if node.getinfo()["testnet"] is True:
        return "testnet"
    else:
        return "mainnet"

def load_p2th_privkeys_into_node(node):
    '''load production p2th privkey into local node'''

    if testnet_or_mainnet(node) is "testnet":
        try:
            node.importprivkey(testnet_PAPROD, "PAPROD")
            assert testnet_PAPROD_addr in node.getaddressesbyaccount("PAPROD")
        except Exception:
            return {"error": "Loading P2TH privkey failed."}
    else:
        try:
            node.importprivkey(mainnet_PAPROD, "PAPROD")
            assert mainnet_PAPROD_addr in node.getaddressesbyaccount("PAPROD")
        except Exception:
            return {"error": "Loading P2TH privkey failed."}

def load_test_p2th_privkeys_into_node(node):
    '''load test p2th privkeys into local node'''

    if testnet_or_mainnet(node) is "testnet":
        try:
            node.importprivkey(testnet_PATEST, "PATEST")
            assert mainnet_PATEST_addr in node.getaddressesbyaccount("PATEST")
        except Exception:
            return {"error": "Loading P2TH privkey failed."}

    else:
        try:
            node.importprivkey(mainnet_PATEST, "PATEST")
            assert mainnet_PAPROD_addr in node.getaddressesbyaccount("PATEST")
        except Exception:
            return {"error": "Loading P2TH privkey failed."}

