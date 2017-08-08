'''all custom exceptions should go here'''


class InvalidDeckIssueModeCombo(Exception):
    '''When verfiying deck issue_mode combinations.'''


class UnsupportedNetwork(Exception):
    '''This network is not suppored by pypeerassets.'''
