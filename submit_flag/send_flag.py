import re

from config import Config
from submit_flag.send import get_flag_info,Send


class SendFlag:
    
    def __init__(self, kv, config: Config, send: Send):
        self.kv = kv
        self.config = config
        self.send = send
        
    async def get_flag_info_for_down(self):
        flag_info = []
        lis = await self.kv.get(f"tasks:", [])
        for li in lis:
            keys = await self.kv.keys_kh(f"p:{li}") # 返回所有以指定字符串开头的键的列表。
            for key in keys:
                r = await self.kv.get(key, {'success': False, 'flag': "", 'err': "", 'ok': False})
                if r['ok']:
                    if r['success']:
                        # p:{uuid}:{name}:{index}
                        name = re.search(fr"^p:{li}:([ \t\S]+):\d+$", key).group(1)
                        flag_info.append(get_flag_info(self.config, name=name, flag=r['flag']))
                await self.kv.delete(key, key)
        return flag_info

    async def send_flag(self, flag_info: Send.FlagInfo | list[Send.FlagInfo]):
        """
        提交 flag 信息（支持单个或多个）。

        Args:
            flag_info (Send.FlagInfo | list[Send.FlagInfo]): flag 信息或列表

        Returns:
            list[tuple[bool, str, str]]: 每个提交的结果 (是否成功, 对应题目, 错误信息)
        """
        results: list[tuple[bool, str, str]] = []

        # 统一转换为列表
        if isinstance(flag_info, Send.FlagInfo):
            flag_info_list = [flag_info]
        else:
            flag_info_list = flag_info

        for fi in flag_info_list:
            try:
                ok, err = await self.send.send_flag(fi)
                results.append((ok, fi.name, err))
            except Exception as ex:
                results.append((False, fi.name, f"Flag发送异常: {str(ex)}"))

        return results
