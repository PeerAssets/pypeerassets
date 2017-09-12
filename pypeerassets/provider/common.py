from pypeerassets.networks import query
from pypeerassets.exceptions import UnsupportedNetwork
from pypeerassets.constants import param_query
from pypeerassets.networks import query
import requests


class Provider:

    @staticmethod
    def _netname(name: str) -> dict:
        '''resolute network name,
        required because some providers use shortnames and other use longnames.'''

        try:
            long = query(name).network_name
            short = query(name).network_shortname
        except AttributeError:
            raise UnsupportedNetwork('''This blockchain network is not supported by the pypeerassets, check networks.py for list of supported networks.''')

        return {'long': long,
                'short': short}

    @property
    def network(self) -> str:
        '''return network full name'''

        return self._netname(self.net)['long']

    @property
    def network_parameters(self):
        '''load network PeerAssets parameters.'''

        return param_query(self.network)

    @property
    def network_properties(self):
        '''network properties [min_fee, denomination, ...]'''

        return query(self.network)

    @property
    def is_testnet(self) -> bool:
        """testnet or not?"""

        if "testnet" in self.network:
            return True
        else:
            return False

    @classmethod
    def sendrawtransaction(cls, rawtxn: str) -> dict:
        '''sendrawtransaction remote API
        : rawtxn - must be submitted as string'''

        if cls.is_testnet:
            url = 'http://talk.peercoin.net:5555/pushapi/testnet/sendrawtransaction/'
        else:
            url = 'http://talk.peercoin.net:5555/pushapi/sendrawtransaction/'

        resp = requests.get(url + rawtxn)
        return resp.content.decode()
