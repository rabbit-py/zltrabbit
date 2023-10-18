# -*- coding: utf-8 -*-

from urllib.parse import urlparse, ParseResult


def url_parse(url: str) -> ParseResult:
    if '@' in url:
        scheme, _, opts = url.rpartition('://')
        auth, _, opts = opts.rpartition('@')
        username, password = auth.split(':')
        parsed = urlparse(f'{scheme}://{opts}')
    else:
        parsed = urlparse(url)
        username = parsed.username
        password = parsed.password
    return ParseResult(
        scheme=parsed.scheme,
        netloc=f"{username if username else ''}"
        + f"{':'+password+'@' if password else ''}"
        + f'{parsed.hostname}:{parsed.port}',
        path=parsed.path,
        params=parsed.params,
        query=parsed.query,
        fragment=parsed.fragment,
    )
