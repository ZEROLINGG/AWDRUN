import json
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import aiohttp
from aiohttp import ClientResponse, ClientSession

from config import Config


class Send:
    headers = {
        'Host': '',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Connection': 'keep-alive',
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'matchId': '',
    }

    def __init__(self, url: str, timeout: int = 10, usehttp: bool = False):
        """
        初始化 AsyncSend 类，设置基础 URL 和默认超时时间。

        Args:
            url (str): 主机地址，例如 'http://example.com' 或 'example.com'
            timeout (int): 请求超时时间（秒），默认为 10 秒
            usehttp (bool): 是否强制使用 http 协议
        """
        # 补全协议
        if not url.startswith(('http://', 'https://')):
            if usehttp:
                url = f'http://{url}'
            else:
                url = f'https://{url}'
        # 去除末尾斜杠
        url = url.rstrip('/')
        # 验证 URL 格式
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL format: {url}")

        self.base_url = parsed_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[ClientSession] = None
        self._session_headers = self.headers.copy()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def _ensure_session(self):
        """确保 session 已创建"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=False)  # 如需要 SSL 验证可设为 True
            self.session = aiohttp.ClientSession(
                headers=self._session_headers,
                timeout=self.timeout,
                connector=connector
            )

    def set_header(self, key: str, value: str) -> None:
        """
        设置或更新单个 header。

        Args:
            key (str): header 键
            value (str): header 值
        """
        self._session_headers[key] = value
        if self.session and not self.session.closed:
            self.session.headers[key] = value

    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        批量设置或更新 headers。

        Args:
            headers (Dict[str, str]): 要更新的 headers 字典
        """
        self._session_headers.update(headers)
        if self.session and not self.session.closed:
            self.session.headers.update(headers)

    async def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> ClientResponse:
        """
        发送异步 GET 请求。

        Args:
            endpoint (str): API 端点路径
            params (Optional[Dict]): 查询参数
            headers (Optional[Dict]): 自定义 headers
            **kwargs: 其他 aiohttp 参数

        Returns:
            ClientResponse: 响应对象
        """
        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"

        async with self.session.get(url, params=params, headers=headers, **kwargs) as response:
            # 读取响应内容以避免连接被提前关闭
            await response.read()
            return response

    async def post(self, endpoint: str, data: Dict = None, headers: Optional[Dict] = None, useform: bool = False, **kwargs) -> ClientResponse:
        """
        发送异步 POST 请求。

        Args:
            endpoint (str): API 端点路径
            data (Optional[Dict]): 请求体数据
            headers (Optional[Dict]): 自定义 headers
            useform (bool): 是否使用表单方案
            **kwargs: 其他 aiohttp 参数

        Returns:
            ClientResponse: 响应对象
        """
        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"

        if not useform:
            if isinstance(data, dict):
                kwargs['json'] = data
            else:
                kwargs['data'] = data
        else:
            kwargs['data'] = data

        async with self.session.post(url, headers=headers, **kwargs) as response:
            # 读取响应内容以避免连接被提前关闭
            await response.read()
            return response

    async def close(self) -> None:
        """
        关闭 Session，释放连接。
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    @dataclass
    class FlagInfo:
        """Flag提交信息类"""
        endpoint: str
        data: Optional[Dict] = None
        headers: Optional[Dict] = None
        params: Optional[Dict] = None
        method: str = "POST"
        name: str = ""

    async def send_flag(self, flag_info: FlagInfo) -> tuple[bool, str]:
        """
        异步发送 flag。

        Args:
            flag_info (FlagInfo): flag 信息

        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            if flag_info.method == "POST":
                response = await self.post(flag_info.endpoint, data=flag_info.data, headers=flag_info.headers)
                if flag_info.params:
                    # 如果需要同时传递 params，需要手动构造 URL
                    import urllib.parse
                    query_string = urllib.parse.urlencode(flag_info.params)
                    endpoint_with_params = f"{flag_info.endpoint}?{query_string}"
                    response = await self.post(endpoint_with_params, data=flag_info.data, headers=flag_info.headers)
            elif flag_info.method == "GET":
                response = await self.get(flag_info.endpoint, params=flag_info.params, headers=flag_info.headers)
            else:
                return False, f"Invalid flag method: {flag_info.method}"

            # 检查 HTTP 状态码
            response.raise_for_status()

            try:
                # 尝试解析 JSON
                result = await response.json()
            except (ValueError, json.JSONDecodeError):
                # 如果不是 JSON，读取文本内容
                result = await response.text()

            if isinstance(result, dict):
                field = ["data", "code", "message", "info", "msg"]
                for f in field:
                    field_value = str(result.get(f, "")).lower()
                    if field_value in ["ok", "success", "成功"]:
                        return True, ""
                    if field_value in ["error", "错误", "重新提交", "失败"]:
                        return False, json.dumps(result, ensure_ascii=False)
                return False, "[未能解析的结果]：\n" + json.dumps(result, ensure_ascii=False)

            if isinstance(result, str):
                field_success = ["ok", "success", "成功"]
                field_error = ["error", "错误", "重新提交", "失败"]
                result_lower = result.lower()

                for f in field_success:
                    if f in result_lower:
                        return True, ""

                for f in field_error:
                    if f in result_lower:
                        return False, result
                return False, "[未能解析的结果]：\n" + result

            try:
                # 读取原始字节内容并转为十六进制
                content_bytes = await response.read()
                result = content_bytes.hex()
                field_success = ["6f6b", "73756363657373", "e68890e58a9f"]
                field_error = ["6572726f72", "e99499e8afaf", "e9878de696b0e68f90e4baa4", "e5a4b1e8b4a5"]

                for f in field_success:
                    if f in result:
                        return True, ""

                for f in field_error:
                    if f in result:
                        return False, result
                return False, "[未能解析的结果]：\n" + result

            except Exception as ex:
                return False, str(ex)

        except aiohttp.ClientError as ex:
            return False, f"请求错误: {str(ex)}"
        except asyncio.TimeoutError:
            return False, "请求超时"
        except Exception as ex:
            return False, str(ex)


def get_flag_info(config: Config, name: str, flag: str, **kwargs) -> Send.FlagInfo:
    """
    根据 config.flag_info 构造 Send.FlagInfo（headers, data, params）。
    支持通过 kwargs 提供 'overrides'，格式示例:
        overrides = {
            "headers": {"X-Custom": "val"},
            "data": {"exerciseId": 123},
            "params": {"debug": "1"}
        }
    覆盖优先级：overrides > once(part) > base(part) > default None
    """
    def sj_get(cfg: Config, subject_name: str, field: str) -> Optional[Any]:
        for sj in getattr(cfg, "subject", []) or []:
            if sj.get("name") == subject_name:
                return sj.get(field)
        return None

    overrides = kwargs.get("overrides", {})
    h: Dict[str, Any] = {}
    d: Dict[str, Any] = {}
    p: Dict[str, Any] = {}

    for fi in getattr(config, "flag_info", []) or []:
        part = fi.get("part")
        # 遍历字段键值
        for key, spec in fi.items():
            if key == "part":
                continue
            if not isinstance(spec, dict):
                continue  # 非法 spec，跳过
            hdp = str(spec.get("hdp", "")).lower()
            # 决定值的来源
            value = None
            if part == "base":
                value = spec.get("default")
            elif part == "once":
                if key == "flag":
                    value = flag
                else:
                    value = sj_get(config, name, key)
            else:
                # 未知 part，可扩展或跳过
                continue

            # 若 overrides 明确指定，则覆盖
            if key in overrides.get("headers", {}):
                if "h" in hdp:
                    h[key] = overrides["headers"][key]
            if key in overrides.get("data", {}):
                if "d" in hdp:
                    d[key] = overrides["data"][key]
            if key in overrides.get("params", {}):
                if "p" in hdp:
                    p[key] = overrides["params"][key]

            # 否则使用计算得到的 value（当 value 不是 None 时）
            if value is not None:
                if "h" in hdp:
                    h.setdefault(key, value)
                if "d" in hdp:
                    d.setdefault(key, value)
                if "p" in hdp:
                    p.setdefault(key, value)

    # 如果希望对空 dict 传 None：
    headers_final = h or None
    data_final = d or None
    params_final = p or None

    return Send.FlagInfo(endpoint=config.flag_endpoint,
                              data=data_final,
                              headers=headers_final,
                              params=params_final,
                              name=name
                         )


# 使用示例
async def example_usage():
    """使用示例"""
    # 方式1：使用异步上下文管理器（推荐）
    async with Send("https://example.com", timeout=30) as client:
        client.set_header("Authorization", "Bearer your_token")

        # GET 请求
        response = await client.get("/api/data", params={"page": 1})
        data = await response.json()
        print(data)

        # POST 请求
        response = await client.post("/api/submit", data={"key": "value"})
        result = await response.text()
        print(result)

    # 方式2：手动管理生命周期
    client = Send("https://example.com")
    try:
        response = await client.get("/api/test")
        print(await response.text())
    finally:
        await client.close()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
    