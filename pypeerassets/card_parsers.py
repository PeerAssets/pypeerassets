'''parse cards according to deck issue mode'''

from .pautils import exponent_to_amount


def none_parser(cards):
    '''parser for NONE [0] issue mode'''

    return None


def custom_parser(cards, parser=None):
    '''parser for CUSTOM [1] issue mode,
    please provide your custom parser as argument'''

    if not parser:
        return cards

    else:
        return parser(cards)


def once_parser(cards):
    '''parser for ONCE [2] issue mode'''

    return [next(i for i in cards if i.type == "CardIssue")]


def multi_parser(cards):
    '''parser for MULTI [4] issue mode'''

    return cards


def mono_parser(cards):
    '''parser for MONO [8] issue mode'''

    return [i for i in cards if i.type == "CardIssue"
            and exponent_to_amount(i.amount[0], i.number_of_decimals) == 1]


def unflushable_parser(cards):
    '''parser for UNFLUSHABLE [16] issue mode'''

    return [i for i in cards if i.type == "CardIssue"]
