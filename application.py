from dataclasses import dataclass

from config import Config
from kv import Kv

@dataclass
class Paths:
    pass

    
class AwdRun:
    
    def __init__(self):
        self.kv = Kv()
        self.config = Config()
        
        
        