'''Common provider class with basic features.'''

from abc import ABC, abstractmethod
from pypeerassets.exceptions import UnsupportedNetwork
from pypeerassets.pa_constants import PAParams, param_query
from pypeerassets.networks import NetworkParams, net_query
import requests


class Provider(ABC):

    @staticmethod
    def _netname(name: str) -> dict:
        '''resolute network name,
        required because some providers use shortnames and other use longnames.'''

        try:
            long = net_query(name).network_name
            short = net_query(name).network_shortname
        except AttributeError:
            raise UnsupportedNetwork('''This blockchain network is not supported by the pypeerassets, check networks.py for list of supported networks.''')

        return {'long': long,
                'short': short}

    @property
    def network(self) -> str:
        '''return network full name'''

        return self._netname(self.net)['long']

    @property
    def pa_parameters(self) -> PAParams:
        '''load network PeerAssets parameters.'''

        return param_query(self.network)

    @property
    def network_properties(self) -> NetworkParams:
        '''network parameters [min_fee, denomination, ...]'''

        return net_query(self.network)

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

    @abstractmethod
    def getblockhash(self, blocknum: int) -> str:
        '''get blockhash using blocknum query'''
        raise NotImplementedError

    @abstractmethod
    def getblockcount(self) -> int:
        '''get block count'''
        raise NotImplementedError

    @abstractmethod
    def getblock(self) -> dict:
        '''query block using <blockhash> as key.'''
        raise NotImplementedError

    @abstractmethod
    def getdifficulty(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def getbalance(self, address: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def getreceivedbyaddress(self, address: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def listunspent(self, address: str) -> list:
        raise NotImplementedError

    @abstractmethod
    def select_inputs(self, address: str, amount: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def getrawtransaction(self, txid: str, decrypt=1) -> dict:
        raise NotImplementedError

    @abstractmethod
    def listtransactions(self, address: str) -> list:
        raise NotImplementedError
