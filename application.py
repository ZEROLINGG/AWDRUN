from dataclasses import dataclass

from config import Config
from get_flag.attack import Attack
from kv import Kv
from submit_flag.send import Send


@dataclass
class Paths:
    pass

    
class AwdRun:
    
    def __init__(self):
        self.kv = Kv()  # 键值对存储
        self.config = Config()  # 自动化配置
        self.send = Send(self.config.flag_ip)   # flag提交工具
        self.attack = Attack(self.kv)   # 基础攻击工具

        self.send.set_headers(self.config.auth_headers)
        
        
        
        