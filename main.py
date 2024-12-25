# coding：utf-8
from typing import List
from asyncio import get_event_loop, ensure_future
from json import loads
from sys import exit
from util import read_file
from trick import TcpTrickServer, UdpTrickServer, TrickServer


class Entry:
    """入口类"""

    def __init__(self):
        self._loop = get_event_loop()
        self._trick_servers: List[TrickServer] = []
        self._trick_infos = []
        self._read_config()

    def _read_config(self):
        """读取配置"""
        config_data = read_file("trick_info.json")
        if not config_data:
            print("config info is None!")
            exit(1)
        self._trick_info = loads(config_data)

    def start(self):
        """启动欺骗服务"""

        for item in self._trick_info:
            if item["protocol"].lower() == "tcp":
                self._trick_servers.append(TcpTrickServer(item["port"], item["probe_datas"], item["resp_datas"]))
            elif item["protocol"].lower() == "udp":
                self._trick_servers.append(UdpTrickServer(item["port"], item["probe_datas"], item["resp_datas"]))
            else:
                continue
        if not self._trick_servers:
            print("no available config")
            exit(0)

        for server in self._trick_servers:
            ensure_future(server.start())
        self._loop.run_forever()

    def stop(self):
        """停止欺骗服务"""
        for server in self._trick_servers:
            server.close()
        self._loop.stop()
        self._loop.close()


if __name__ == "__main__":
    Entry().start()