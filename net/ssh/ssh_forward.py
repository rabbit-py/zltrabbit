# -*- coding: utf-8 -*-
import asyncssh
import asyncio


class SSHForward:
    @property
    def tunnel(self) -> asyncssh.SSHListener:
        return self._tunnel

    def __init__(self, host='', port=22, username='', password='', forward_host='127.0.0.1', forward_port=0, key=None) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._forward_host = forward_host
        self._forward_port = forward_port
        self._key = key

    async def run(self) -> int:
        ssh_conn = await asyncssh.connect(
            self._host, port=self._port, username=self._username, password=self._password, client_keys=self._key
        )
        self._tunnel = await ssh_conn.forward_local_port('', 0, self._forward_host, self._forward_port)
        asyncio.ensure_future(self.tunnel.wait_closed())
        asyncio.ensure_future(ssh_conn.wait_closed())
        return self._tunnel.get_port()
