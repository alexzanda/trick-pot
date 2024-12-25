# coding：utf-8
import os.path
from typing import Optional
from os.path import exists
from asyncio import Future, ensure_future
from functools import wraps, partial
from inspect import isawaitable
from logging import handlers, INFO, getLogger, StreamHandler
from netifaces import ifaddresses, AF_INET, AF_INET6


def create_logger(name: str, log_level=INFO, handler = StreamHandler()):
    """创建日志记录器"""
    logger = getLogger(name)
    if not handler:
        handler = StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger


def launcher(func):
    """异步装饰器"""

    def coro_logger(func_name: str, future: Future):
        """协程异常捕获器"""
        try:
            future.set_result()
        except Exception as e:
            create_logger("launcher_log").exception(f"uncaught exception in async function {func_name}, {e.__str__()}")

    @wraps(func)
    def wrapper(*args, **kwargs) -> object:
        result = func(*args, **kwargs)
        if isawaitable(result):
            task = ensure_future(result)
            task.add_done_callback(partial(coro_logger, func.__name__))
            result = task
        return result
    return wrapper


def read_file(file_path: str, mode="rb") -> Optional[bytes]:
    """读取文件内容"""
    if not exists(file_path):
        return None

    with open(file_path, mode=mode) as f:
        return f.read()


def get_bus_ip(version: int = 4):
    """获取当前服务所在机器的业务ip，也即被代理钱的ip"""
    # 从当前路径下获取配置信息
    iface = "eth0"
    if os.path.exists("iface"):
        with open("iface", mode="r") as f:
            iface = f.read()

    addresses = ifaddresses(iface)

    if version == 4:
        ipv4_infos = addresses.get(AF_INET, [])
        if ipv4_infos:
            return ipv4_infos[0]["addr"]
    else:
        ipv6_infos = addresses.get(AF_INET6, [])
        if ipv6_infos:
            return ipv6_infos[0]["addr"].partition("%")[0]