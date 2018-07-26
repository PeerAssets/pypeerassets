import pytest

from pypeerassets.exceptions import UnsupportedNetwork
from pypeerassets.networks import net_query


def test_net_query():
    "Check that we can find NetworkParams for networks by name."

    # Use a network's long name
    net_params = net_query("peercoin")
    assert net_params.shortname == "ppc"

    # Use a network's short name
    net_params = net_query("tppc")
    assert net_params.name == "peercoin-testnet"

    # Try to find a network we don't know about.
    with pytest.raises(UnsupportedNetwork):
        net_query("not a network name we know of.")
