import pytest

from pypeerassets.exceptions import UnsupportedNetwork
from pypeerassets.pa_constants import param_query


def test_param_query():
    "Check that we can find PAParams for networks by name."

    # Use a network's long name
    pa_params = param_query("peercoin")
    assert pa_params.network_shortname == "ppc"

    # Use a network's short name
    pa_params = param_query("tppc")
    assert pa_params.network_name == "peercoin-testnet"

    # Try to find a network we don't know about.
    with pytest.raises(UnsupportedNetwork):
        param_query("not a network name we know")
