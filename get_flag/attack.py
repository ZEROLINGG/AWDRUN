"""grt_flag/attack.py"""
"""grt_flag/attack.py"""
import asyncio
import datetime
import importlib
import importlib.util
from importlib.machinery import ModuleSpec
from kv import Kv
import uuid
import aiofiles
from pathlib import Path
from typing import Any, Coroutine, List, Optional, Dict


class Attack:

    def __init__(self, kv: Kv, subject_dir: str = str(Path(__file__).resolve().parent / "subject"),
                 default_timeout: float = 60.0 * 3):
        self._tasks: Dict[str, List[asyncio.Task]] = {}
        self.sj_dir = Path(subject_dir)
        self.kv = kv    # kv是一个异步且线程安全的键值存储器
        self._log_lock = asyncio.Lock()
        self.default_timeout = default_timeout

    async def _get_ip(self, name: str) -> list[str]:
        path = self.sj_dir / name / "ip.txt"
        if not path.exists():
            return []
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            lines = await f.readlines()
            return [line.strip() for line in lines if line.strip()]

    def _get_spec(self, name: str) -> Optional[ModuleSpec]:
        path = self.sj_dir / name / "Payload.py"
        if not path.exists():
            return None
        spec = importlib.util.spec_from_file_location("Payload", str(path))
        return spec

    async def get_payloads(self, name: str, timeout: float = None) -> Optional[tuple[str, list[Coroutine[Any, Any, None]], int]]:
        log = self.sj_dir / name / "log.txt"
        spec = self._get_spec(name)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _uuid = uuid.uuid4().hex

        # 使用传入的超时或默认超时
        timeout = timeout or self.default_timeout

        async def payload_coro(ip: str, i: int):
            r = {'success': False, 'flag': "", 'err': "", 'ok': False}
            await self.kv.add(f"p:{_uuid}:{name}:{i}", r)  # 会在另一个监控线程中使用到

            async def execute_payload():
                try:
                    payload = module.Payload(ip)
                    # 优先使用异步方法
                    if hasattr(payload, "run_async") and callable(payload.run_async):
                        return await payload.run_async() #type:ignore
                    elif hasattr(payload, "run") and callable(payload.run):
                        # 如果只有同步方法，在执行器中运行以避免阻塞
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, payload.run, ())
                    else:
                        return False, "", "[无payload.run()或payload.run_async()]"
                except Exception as ex:
                    return False, "", f"[实例化类错误或run_async错误]{str(ex)}"
            try:
                # 使用 wait_for 添加超时控制
                success, flag, err = await asyncio.wait_for(
                    execute_payload(),
                    timeout=timeout
                )
                r.update({'success': success, 'flag': flag, 'err': err, 'ok': True})
            except asyncio.TimeoutError:
                r.update({'err': f'Timeout after {timeout} seconds', 'ok': True})
            except Exception as e:
                r.update({'err': str(e), 'ok': True})
            # 写日志
            log_msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {ip}, Task: {i}\n{r}\n{'~'*20}\n"
            async with self._log_lock:
                async with aiofiles.open(log, "a", encoding="utf-8") as f:
                    await f.write(log_msg)
            await self.kv.add(f"p:{_uuid}:{name}:{i}", r)

        ips = await self._get_ip(name)
        tasks = [payload_coro(ip, i) for i, ip in enumerate(ips)]
        return _uuid, tasks, len(ips)

    async def run_payloads(self, name: str, timeout: float = None) -> tuple[str, int]:
        """异步运行 payloads - 主要接口"""
        result = await self.get_payloads(name, timeout)
        if result is None:
            return "", 0
        _uuid, coros, num = result

        
        # try:
        #     asyncio.get_running_loop()
        # except RuntimeError:
        #     # 如果没有运行的事件循环，创建一个新的
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)

        task_list = [asyncio.create_task(coro) for coro in coros]
        self._tasks[_uuid] = task_list
        # 在后台运行任务，不阻塞
        lis = await self.kv.get(f"tasks:", [])
        lis.extend(_uuid)
        await self.kv.add(f"tasks:", lis)
        return _uuid, num

    async def await_tasks(self, _uuid: str) -> list[Any]:
        """等待指定 UUID 的所有任务完成"""
        if _uuid not in self._tasks:
            return []

        tasks = self._tasks[_uuid]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def cancel(self, _uuid: str) -> bool:
        """取消指定任务 UUID 的所有 Payload"""
        if _uuid not in self._tasks:
            return False

        tasks = self._tasks[_uuid]
        for task in tasks:
            if not task.done():
                task.cancel()
        return True

    async def cleanup_completed(self, _uuid: str) -> bool:
        """清理已完成的任务"""
        if _uuid not in self._tasks:
            return False

        tasks = self._tasks[_uuid]
        all_done = all(task.done() for task in tasks)
        if all_done:
            del self._tasks[_uuid]
            return True
        return False

    def cleanup_all_completed(self) -> List[str]:
        """清理所有已完成的任务，返回被清理的 UUID 列表"""
        cleaned = []
        for _uuid in list(self._tasks.keys()):
            tasks = self._tasks[_uuid]
            all_done = all(task.done() for task in tasks)
            if all_done:
                del self._tasks[_uuid]
                cleaned.append(_uuid)
        return cleaned
    