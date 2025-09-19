import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests import Response

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
    def __init__(self, url: str, port: int = 80, timeout: int = 10):
        """
        初始化 Send 类，设置基础 URL 和默认超时时间。

        Args:
            url (str): 主机地址，例如 'http://example.com' 或 'example.com'
            port (int): 端口号，默认为 80
            timeout (int): 请求超时时间（秒），默认为 10 秒
        """
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'  # 默认 HTTPS
        url = url.rstrip('/')  # 去除末尾斜杠
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL format: {url}")
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}:{port}" if port != 80 and port != 443 else f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def set_header(self, key: str, value: str) -> None:
        """
        设置或更新单个 header。

        Args:
            key (str): header 键
            value (str): header 值
        """
        self.session.headers[key] = value

    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        批量设置或更新 headers。

        Args:
            headers (Dict[str, str]): 要更新的 headers 字典
        """
        self.session.headers.update(headers)


    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> Response:
        """
        发送 GET 请求。

        Args:
            endpoint (str): API 端点路径
            params (Optional[Dict]): 查询参数
            headers (Optional[Dict]): 自定义 headers
            **kwargs: 其他 requests 参数

        Returns:
            response: response 数据
        """
        r = self.session.get(f"{self.base_url}{endpoint}", params=params, headers=headers, timeout=self.timeout, **kwargs)
        return r

    def post(self, endpoint: str, data: Dict|None, headers: Optional[Dict] = None, useform:bool=False, **kwargs) -> Response:
        """
        发送 POST 请求。

        Args:
            endpoint (str): API 端点路径
            data (Optional[Dict]): 请求体数据
            headers (Optional[Dict]): 自定义 headers
            useform (bool): 是否使用表单方案
            **kwargs: 其他 requests 参数

        Returns:
            response: response 数据
        """
        if not useform:
            if isinstance(data, dict):
                kwargs['json'] = data
            else:
                kwargs['data'] = data
        else:
            kwargs['data'] = data
            
        r = self.session.post(f"{self.base_url}{endpoint}", headers=headers, timeout=self.timeout, **kwargs)
        return r


    def close(self) -> None:
        """
        关闭 Session，释放连接。
        """
        self.session.close()
        
    
    @dataclass
    class FlagInfo:
        """Flag提交信息类"""
        endpoint: str
        data: Optional[Dict] = None
        headers: Optional[Dict] = None
        params: Optional[Dict] = None
        method: str = "POST"
    
    def send_flag(self, flag_info: FlagInfo) -> tuple[bool, str]:
        try:
            if flag_info.method == "POST":
                r = self.post(flag_info.endpoint, data=flag_info.data, headers=flag_info.headers, params=flag_info.params)
            elif flag_info.method == "GET":
                r = self.get(flag_info.endpoint, params=flag_info.params, headers=flag_info.headers)
            else:
                return False,f"Invalid flag method: {flag_info.method}"
            r.raise_for_status()
            try:
                result = r.json()
            except (ValueError, json.decoder.JSONDecodeError):
                result = r.content.decode(errors="ignore")

            if isinstance(result, dict):
                field = ["data", "code", "message", "info", "msg"]
                for f in field:
                    if str(result.get(f, "")).lower() in ["ok", "success", "成功"]:
                        return True, ""
                    if str(result.get(f, "")).lower() in ["error", "错误", "重新提交", "失败"]:
                        return False, json.dumps(result)
                return False, "[未能解析的结果]：\n" + json.dumps(result)
            if isinstance(result, str):
                field_success = ["ok", "success", "成功"]
                field_error = ["error", "错误", "重新提交", "失败"]
                for f in field_success:
                    if f in result.lower():
                        return True, ""
                    
                for f in field_error:
                    if f in result.lower():
                        return False, result
                return False, "[未能解析的结果]：\n" + result
            
            try:
                result = r.content.hex()
                field_success = ["6f6b", "73756363657373", "e68890e58a9f"]
                field_error = ["error","e99499e8afaf","e9878de696b0e68f90e4baa4","e5a4b1e8b4a5"]
                for f in field_success:
                    if f in result:
                        return True, ""

                for f in field_error:
                    if f in result:
                        return False, result
                return False, "[未能解析的结果]：\n" + result
            
            except Exception as ex:
                return False, str(ex)
        
        except Exception as ex:
            return False,str(ex)


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
                         params=params_final)


        



if __name__ == "__main__":
    pass