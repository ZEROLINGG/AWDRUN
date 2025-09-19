import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests import Response


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
            if flag_info.method == "post":
                r = self.post(flag_info.endpoint, data=flag_info.data, headers=flag_info.headers, params=flag_info.params)
            elif flag_info.method == "get":
                r = self.get(flag_info.endpoint, params=flag_info.params, headers=flag_info.headers)
            else:
                return False,f"Invalid flag mod: {flag_info.method}"
            r.raise_for_status()
            try:
                result = r.json()
            except json.decoder.JSONDecodeError:
                result = r.text

            if isinstance(result, dict):
                if str(result.get("status", "")).lower() in ["ok", "success", "成功"]:
                    return True, ""
                return False, json.dumps(result)
            if ("success" in result.lower()) or ("ok" in result.lower()) or ("成功" in result):
                return True, ""
            return False, result
        
        except Exception as ex:
            return False,str(ex)
            
        
        

        



if __name__ == "__main__":
    pass