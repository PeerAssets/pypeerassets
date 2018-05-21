import pytest
from pypeerassets import base58


def test_b58encode():

    assert base58.b58encode("hello".encode()) == 'Cn8eVZg'


def test_b58decode():

    assert base58.b58decode('Cn8eVZg') == b'hello'
