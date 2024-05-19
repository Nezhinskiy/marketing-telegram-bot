import python_socks

from config import PROXYS


class Proxy:
    def __init__(self, proxy_str: str) -> None:
        proxy_args = proxy_str.split(':')
        self.addr = proxy_args[0]
        self.port = proxy_args[1]
        self.username = proxy_args[2]
        self.password = proxy_args[3]
        self.proxy_type = python_socks.ProxyType.HTTP

    def get_proxy_dict(self) -> dict:
        return {
            'proxy_type': self.proxy_type,
            'addr': self.addr,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            # 'rdns': True,
        }


class ProxyManager:
    def __init__(self):
        self.proxys_list = []
        for proxy_str in PROXYS:
            self.proxys_list.append(Proxy(proxy_str))

    def get_new_proxy(self):
        if not self.proxys_list:
            return None
        new_proxy = self.proxys_list.pop(0)
        self.proxys_list.append(new_proxy)
        return new_proxy.get_proxy_dict()