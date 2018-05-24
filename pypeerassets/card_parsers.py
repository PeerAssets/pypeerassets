'''parse cards according to deck issue mode'''

from typing import Callable, Optional

from pypeerassets.pautils import exponent_to_amount

def none_parser(cards: list) -> Optional[list]:
    '''
    parser for NONE [0] issue mode
    No issuance allowed.
    '''

    return None


def custom_parser(cards: list, parser: Optional[Callable[[list], Optional[list]]]=None) -> Optional[list]:
    '''parser for CUSTOM [1] issue mode,
    please provide your custom parser as argument'''

    if not parser:
        return cards

    else:
        return parser(cards)


def once_parser(cards: list) -> Optional[list]:
    '''
    parser for ONCE [2] issue mode
    Only one issuance transaction from asset owner allowed.
    '''

    first_issue = next(i for i in cards if i.type == "CardIssue")  # find first CardIssue

    filtered = [i for i in cards if i.type == "CardIssue" if i != first_issue]  #  drop all other CardIssues

    return [i for i in cards if i not in filtered]


def multi_parser(cards: list) -> Optional[list]:
    '''parser for MULTI [4] issue mode'''

    return cards


def mono_parser(cards: list) -> Optional[list]:
    '''
    parser for MONO [8] issue mode
    MONO = 0x08; // All card transaction amounts are equal to 1
    '''

    return [i for i in cards if
            exponent_to_amount(i.amount[0], i.number_of_decimals) == 1]


def unflushable_parser(cards: list) -> Optional[list]:
    '''
    parser for UNFLUSHABLE [16] issue mode
    No card transfer transactions allowed except for the card-issue transaction
    '''

    return [i for i in cards if i.type == "CardIssue"]


parsers = {
    'NONE': none_parser,
    'CUSTOM': custom_parser,
    'ONCE': once_parser,
    'MULTI': multi_parser,
    'MONO': mono_parser,
    'UNFLUSHABLE': unflushable_parser
}
