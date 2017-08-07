from pypeerassets.networks import query
import requests


class Provider:

    @staticmethod
    def _netname(name: str) -> dict:
        '''resolute network name,
        required because some providers use shortnames and other use longnames.'''

        long = query(name).network_name
        short = query(name).network_shortname

        return {'long': long,
                'short': short}

    @property
    def network(self) -> str:
        '''return network full name'''

        return self._netname(self.net)['long']

    @property
    def is_testnet(self) -> bool:
        """testnet or not?"""

        if "testnet" in self.network:
            return True
        else:
            return False

    @classmethod
    def sendrawtransaction(cls, rawtxn: str) -> dict:
        '''sendrawtransaction'''

        url = 'talk.peercoin.net:5555/sendrawtransaction/'
        resp = requests.get(url + rawtxn)
        return resp
