'''Common provider class with basic features.'''

from abc import ABC, abstractmethod
from decimal import Decimal
import urllib.request

from btcpy.structs.address import Address

from pypeerassets.exceptions import UnsupportedNetwork
from pypeerassets.pa_constants import PAParams, param_query
from pypeerassets.networks import NetworkParams, net_query


class Provider(ABC):

    net = ""

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
    def sendrawtransaction(cls, rawtxn: str) -> str:
        '''sendrawtransaction remote API'''

        if cls.is_testnet:
            url = 'https://testnet-explorer.peercoin.net/api/sendrawtransaction?hex={0}'.format(rawtxn)
        else:
            url = 'https://explorer.peercoin.net/api/sendrawtransaction?hex={0}'.format(rawtxn)

        resp = urllib.request.urlopen(url)
        return resp.read().decode('utf-8')

    @abstractmethod
    def getblockhash(self, blocknum: int) -> str:
        '''get blockhash using blocknum query'''
        raise NotImplementedError

    @abstractmethod
    def getblockcount(self) -> int:
        '''get block count'''
        raise NotImplementedError

    @abstractmethod
    def getblock(self, hash: str) -> dict:
        '''query block using <blockhash> as key.'''
        raise NotImplementedError

    @abstractmethod
    def getdifficulty(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def getbalance(self, address: str) -> Decimal:
        raise NotImplementedError

    @abstractmethod
    def getreceivedbyaddress(self, address: str) -> Decimal:
        raise NotImplementedError

    @abstractmethod
    def listunspent(self, address: str) -> list:
        raise NotImplementedError

    @abstractmethod
    def select_inputs(self, address: str, amount: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def getrawtransaction(self, txid: str, decrypt: int=1) -> dict:
        raise NotImplementedError

    @abstractmethod
    def listtransactions(self, address: str) -> list:
        raise NotImplementedError

    def validateaddress(self, address: str) -> bool:
        """Returns True if the passed address is valid, False otherwise. Note
        the limitation that we don't check the address against the underlying
        network (i.e. strict=False). When btcpy can support multiple networks at
        runtime we can be more precise (i.e. strict=True) ;)
        """
        try:
            Address.from_string(address, strict=False)
        except ValueError:
            return False

        return True
