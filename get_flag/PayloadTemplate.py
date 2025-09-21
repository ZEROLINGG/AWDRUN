"""grt_flag/PayloadTemplate.py"""
import time
import sys
import requests

# 每线程独立实例
class Payload:
    # Payload中不要print
    
    def __init__(self, ip:str) -> None:
        self._ip = ip.strip()
    
    
    
    
    
    def run(self) -> tuple[bool, str, str]:
        """自动提交flag框架调用的接口
        Args:
        Returns:
           tuple[bool, str, str]: 返回攻击结果为元组，
                                第一个bool值表示是否成功获取flag，
                                第二个字符串是flag，
                                第三个字符串返回触发的错误或未获得flag的原因
        Raises:
            不抛出错误
        """
        try:
            
            time.sleep(1)
            
            
            return True,"flag{123}","NoError"
        except Exception as e:
            return False,"",str(e)





def console_run() -> None:
    """
    手动测试入口：支持命令行传参或交互式输入IP，调用Payload执行攻击并输出结果。
    适用于手动调试场景。
    """
    _ip = None

    # 优先从命令行参数获取 IP
    if len(sys.argv) > 1 and sys.argv[1].strip():
        _ip = sys.argv[1].strip()
    else:
        # 无参数时提示用户输入
        try:
            _ip = input("请输入要攻击的IP地址：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n用户取消输入。")
            return

    # 校验 IP 是否为空
    if not _ip:
        print("错误：IP地址不能为空。")
        return

    # 实例化 Payload 并执行攻击
    payload = Payload(_ip)
    success, flag, err = payload.run()

    if success:
        print(flag)
    else:
        print("获取flag失败：\n")
        print(err)

if __name__ == "__main__":
    console_run()