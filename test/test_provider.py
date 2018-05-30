import pytest

from pypeerassets.provider import (
    Cryptoid,
    Explorer,
    Mintr,
)


@pytest.mark.parametrize("provider_cls", [Cryptoid, Explorer, Mintr,])
def test_validateaddress_peercoin(provider_cls):
    "Check Providers that can validate Peercoin addresses."

    provider = provider_cls(network='peercoin')

    # Peercoin P2PKH, P2SH addresses.
    assert provider.validateaddress("PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw") is True
    assert provider.validateaddress("p92W3t7YkKfQEPDb7cG9jQ6iMh7cpKLvwK") is True

    # Peercoin Testnet P2PKH address (these _should_ be False, but btcpy cannot
    # support it at the moment).
    assert provider.validateaddress("mj46gUeZgeD9ufU7Fvz2dWqaX6Nswtbpba") is True
    assert provider.validateaddress("n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj") is True

    # Very much not Peercoin addresses.
    assert provider.validateaddress("1BFQfjM29kubskmaAsPjPCfHYphYvKA7Pj") is False
    assert provider.validateaddress("2NFNPUYRpDXf3YXEuVT6AdMesX4kyeyDjtp") is False


@pytest.mark.parametrize("provider_cls", [Cryptoid, Explorer,])
def test_validateaddress_peercoin_testnet(provider_cls):
    "Check Providers that can validate Peercoin Testnet addresses."

    provider = provider_cls(network='peercoin-testnet')

    # Peercoin Testnet P2PKH address.
    assert provider.validateaddress("mj46gUeZgeD9ufU7Fvz2dWqaX6Nswtbpba") is True
    assert provider.validateaddress("n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj") is True

    # Peercoin P2PKH, P2SH addresses (these _should_ be False, but btcpy cannot
    # support it at the moment).
    assert provider.validateaddress("PAdonateFczhZuKLkKHozrcyMJW7Y6TKvw") is True
    assert provider.validateaddress("p92W3t7YkKfQEPDb7cG9jQ6iMh7cpKLvwK") is True

    # Very much not Peercoin Testnet addresses.
    assert provider.validateaddress("1BFQfjM29kubskmaAsPjPCfHYphYvKA7Pj") is False
    assert provider.validateaddress("2NFNPUYRpDXf3YXEuVT6AdMesX4kyeyDjtp") is False
