
'''miscellaneous utilities.'''

def testnet_or_mainnet(node):
    '''check if local node is configured to testnet or mainnet'''

    q = node.getinfo()

    if q["testnet"] is True:
        return "testnet"
    else:
        return "mainnet"

def load_p2th_privkeys_into_node(node):

    if testnet_or_mainnet(node) is "testnet":
        try:
            node.importprivkey(testnet_PAPROD)
            assert testnet_PAPROD_addr in node.getaddressbyaccount()
        except Exception:
            return {"error": "Loading P2TH privkey failed."}
    else:
        try:
            node.importprivkey(mainnet_PAPROD)
            assert mainnet_PAPROD_addr in node.getaddressbyaccount()
        except Exception:
            return {"error": "Loading P2TH privkey failed."}

def load_test_p2th_privkeys_into_node(node):

    if testnet_or_mainnet(node) is "testnet":
        try:
            node.importprivkey(testnet_PATEST)
            assert testnet_PATEST_addr in node.getaddressbyaccount()
        except Exception:
            return {"error": "Loading P2TH privkey failed."}
    else:
        try:
            node.importprivkey(mainnet_PATEST)
            assert mainnet_PATEST_addr in node.getaddressbyaccount()
        except Exception:
            return {"error": "Loading P2TH privkey failed."}

