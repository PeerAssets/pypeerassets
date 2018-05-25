'''all custom exceptions should go here'''


class EmptyP2THDirectory(Exception):
    '''no transactions on this P2TH directory'''


class P2THImportFailed(Exception):
    '''Importing of PeerAssets P2TH privkeys failed.'''


class InvalidDeckIssueModeCombo(Exception):
    '''When verfiying deck issue_mode combinations.'''


class UnsupportedNetwork(Exception):
    '''This network is not suppored by pypeerassets.'''


class InvalidDeckSpawn(Exception):
    '''Invalid deck_spawn, deck is not properly tagged.'''


class InvalidDeckMetainfo(Exception):
    '''Deck metainfo incomplete, deck must have a name.'''


class InvalidDeckVersion(Exception):
    '''Deck version mistmatch.'''


class InvalidDeckIssueMode(Exception):
    '''Deck Issue mode is wrong.'''


class DeckP2THImportError(Exception):
    '''When Deck P2TH import goes wrong.'''


class InvalidCardTransferP2TH(Exception):
    '''card_transfer does not pay to deck p2th in vout[0]'''


class CardVersionMismatch(Exception):
    '''card_transfers version must match deck.version'''


class CardNumberOfDecimalsMismatch(Exception):
    '''card_tranfer number of decimals does not match deck rules.'''


class RecieverAmountMismatch(Exception):
    '''card_transfer list of recievers is not equal to list of amounts'''


class InsufficientFunds(Exception):
    '''this address does not have enough assigned UTXOs'''


class InvalidNulldataOutput(Exception):
    '''mallformed OP_RETURN transaction output.'''


class InvalidVoutOrder(Exception):
    '''mallformed vout sequence'''
