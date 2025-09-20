from dataclasses import dataclass

from config import Config
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
        
        
        
        