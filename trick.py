# coding：utf-8
from typing import List
from random import choice
from base64 import b64decode
from functools import partial
from logging.handlers import RotatingFileHandler
from asyncio import start_server, StreamWriter, StreamReader, sleep, DatagramProtocol, get_event_loop, ensure_future
from util import create_logger, get_bus_ip


event_logger = create_logger("event", handler=RotatingFileHandler("event.log", maxBytes=5*1024*1024, backupCount=5))
com_logger = create_logger("trick")


class TrickServer:

    def __init__(self, trick_port: int, probe_datas: List[str], resp_datas: List[str], host: str = "0.0.0.0"):
        self._host = host
        self._trick_port = trick_port
        self._probe_datas = set([b64decode(item) for item in probe_datas])
        self._resp_datas = resp_datas   # 响应数据中的是原始字节数据的base64
        self._server = None

    async def start(self):
        """启动服务"""
        raise NotImplementedError()

    def close(self):
        """关闭服务"""
        raise NotImplementedError()


class TcpTrickServer(TrickServer):
    """tcp服务伪装"""

    async def start(self):
        """启动欺骗服务"""
        self._server = await start_server(self.handle_conn, host=self._host, port=self._trick_port)
        com_logger.info(f"{self._server} starting")
        await self._server.serve_forever()

    async def handle_conn(self, cl_reader: StreamReader, cl_writer: StreamWriter):
        """处理客户端连接"""
        print("Connection received!")
        data = await cl_reader.read(8192)
        if not data:
            await sleep(0.1)
        print(data)
        src_ip, src_port = cl_reader._transport.get_extra_info("peername")
        dst_ip, dst_port = cl_reader._transport.get_extra_info("sockname")
        event_logger.info(f"{src_ip} {src_port} {dst_ip} {dst_port} tcp service_recognition")

        # 从响应数据
        if self._probe_datas:
            if data in self._probe_datas:
                cl_writer.write(b64decode(choice(self._resp_datas)))
                await cl_writer.drain()
            else:
                cl_writer.close()
        else:
            cl_writer.write(b64decode(choice(self._resp_datas)))
            await cl_writer.drain()

    def close(self):
        """关闭服务"""
        self._server.close()


class UdpServer(DatagramProtocol):
    """基础udp服务器"""

    def __init__(self, probe_datas: List[str], resp_datas: List[str]):
        super().__init__()
        self._probe_datas = probe_datas
        self._resp_datas = resp_datas

    def connection_made(self, transport):
        """连接建立"""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: str):
        """接收到数据"""
        send = b64decode(choice(self._resp_datas))
        src_ip, src_port = addr
        dst_ip, dst_port = self.transport.get_extra_info("sockname")
        if dst_ip == "0.0.0.0":
            dst_ip = get_bus_ip(version=4 if ":" not in src_ip else 6)
        event_logger.info(f"{src_ip} {src_port} {dst_ip} {dst_port} udp service_recognition")

        if self._probe_datas:
            if data in self._probe_datas:
                self.transport.sendto(send, addr)
        else:
            self.transport.sendto(send, addr)

    def close(self):
        """关闭服务"""
        self.transport.close()


class UdpTrickServer(TrickServer):
    """udp服务模拟器"""

    async def start(self):
        """启动欺骗服务"""
        self._loop = get_event_loop()
        _, self._server = await self._loop.create_datagram_endpoint(partial(UdpServer, self._probe_datas, self._resp_datas), local_addr=(self._host, self._trick_port))
        com_logger.info(f"{self._server} starting")

    def close(self):
        """关闭服务"""
        self._server.close()