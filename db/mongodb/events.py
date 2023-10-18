# -*- coding: utf-8 -*-
from urllib.parse import urlparse, urlunparse, ParseResult
from base.di.service_location import service


async def sshforward_event(param: dict) -> int:
    url: str = param.get('url')
    if '@' in url:
        scheme, _, opts = url.rpartition('://')
        auth, _, opts = opts.rpartition('@')
        username, password = auth.split(':')
        parsed = urlparse(f'{scheme}://{opts}')
    else:
        parsed = urlparse(url)
        username = parsed.username
        password = parsed.password
    sshtunnel = param.pop('sshtunnel', None)
    if sshtunnel:
        sshtunnel.update({'forward_host': parsed.hostname, 'forward_port': parsed.port})
        sshtunnel = service.create(sshtunnel.pop('()', None), sshtunnel, False)
        port = await sshtunnel.run()
        url = urlunparse(
            ParseResult(
                scheme=parsed.scheme,
                netloc=f"{username if username else ''}" + f"{':'+password+'@' if password else ''}" + f'localhost:{port}',
                path=parsed.path,
                params=parsed.params,
                query=parsed.query,
                fragment=parsed.fragment,
            )
        )
        param.update({'url': url})
