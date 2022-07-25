from base64 import b64encode
from urllib.parse import urlparse, ParseResult, urljoin

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import requests

from dogeek_cli.config import config


class Client(requests.Session):
    def __init__(self, registry, *a, **kw):
        super().__init__(*a, **kw)
        self.pub_key_str: str = (config.app_path / 'key.pub').read_text()
        self.pub_key = serialization.load_ssh_public_key(self.pub_key_str.encode('utf8'))
        self.priv_key_str: str = (config.app_path / 'key').read_text()
        self.priv_key: rsa.RSAPrivateKey = serialization.load_pem_private_key(
            self.priv_key_str.encode('utf8'), None
        )
        self.headers['Authorization'] = self.pub_key_str
        self.headers['X-Maintainer-Email'] = config['app.email']
        self.registry = registry

    def make_signature(self, url: str) -> str:
        url: ParseResult = urlparse(url)
        signature = self.priv_key.sign(
            url.path.encode('utf8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return b64encode(signature).decode('utf8')

    def request(self, method: str, url: str, **kw):
        do_sign = kw.pop('do_sign', False)
        headers = kw.pop('headers', {})
        url = url.lstrip('/')
        if self.registry == 'localhost':
            url = urljoin('http://0.0.0.0:8000', url)
        else:
            url = urljoin(f'https://{self.registry}', url)
        if do_sign:
            headers['X-Signature'] = self.make_signature(url)
        return super().request(method, url, headers=headers, **kw)

    def get(self, url, **kw):
        return self.request('GET', url, **kw)

    def post(self, url, **kw):
        return self.request('POST', url, **kw)

    def patch(self, url, **kw):
        return self.request('PATCH', url, **kw)

    def put(self, url, **kw):
        return self.request('PUT', url, **kw)

    def delete(self, url, **kw):
        return self.request('DELETE', url, **kw)
