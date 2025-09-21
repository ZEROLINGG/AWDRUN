"""grt_flag/attack.py"""
import asyncio
import datetime
import importlib,importlib.util
from importlib.machinery import ModuleSpec
from kv import Kv
import threading,uuid,aiofiles
from pathlib import Path
from typing import Any, Coroutine, List


class Attack:
    
    def __init__(self, kv:Kv, subject_dir:str=str(Path(__file__).resolve().parent)):
        self.sj_dir = Path(subject_dir)
        self.kv = kv
        self._log_lock = asyncio.Lock()


    def _get_ip(self, name:str) -> list[str]:
        path = self.sj_dir / name / "ip.txt"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    
    def _get_spec(self, name:str) -> ModuleSpec | None:
        path = self.sj_dir / name / "Payload.py"
        if not path.exists():
            return None
        spec = importlib.util.spec_from_file_location("Payload", str(path))
        return spec
    
    def get_payloads(self, name:str) -> tuple[str, list[Coroutine[Any, Any, None]], int] | None:
        log = self.sj_dir / name / "log.txt"
        spec = self._get_spec(name)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _uuid = uuid.uuid4().hex
        async def payload_coro(ip:str,i:int):
            r = {'success': False, 'flag': "", 'err': "", 'ok': False}
            await self.kv.add(f"p:{_uuid}:{i}", r)
            try:
                payload = module.Payload(ip)
                # 优先使用异步方法
                if hasattr(payload, "run_async") and callable(payload.run_async):
                    success, flag, err = await payload.run_async() #type:Ignore
                elif hasattr(payload, "run") and callable(payload.run):
                    success, flag, err = payload.run()
                else:
                    success, flag, err = (False, "", "[无payload.run()或payload.run_async()]")
                r.update({'success': success, 'flag': flag, 'err': err, 'ok': True})
            except Exception as e:
                r.update({'err': str(e), 'ok': True})
            # 写日志
            log_msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {ip}, Task: {i}\n{r}\n{'~'*20}\n"
            async with self._log_lock:  # 异步锁保护
                async with aiofiles.open(log, "a", encoding="utf-8") as f:
                    await f.write(log_msg)
            await self.kv.add(f"p:{_uuid}:{i}", r)
            
        ips = self._get_ip(name)
        tasks = [payload_coro(ip, i) for i, ip in enumerate(ips)]
        return _uuid,tasks,len(ips)
        
    def run_payloads(self, name:str):
        def runs(tas):
            asyncio.run(asyncio.gather(*tas)) #type:Ignore
        _uuid,tasks,num = self.get_payloads(name)
        if tasks is None:
            return "",0
        thread = threading.Thread(target=lambda: runs(tasks))
        thread.start()
        return _uuid,num
        