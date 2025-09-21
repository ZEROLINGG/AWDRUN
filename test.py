import time  # 导入时间模块，用于模拟任务延迟
import threading  # 导入线程模块（在此代码中未直接使用，但可用于并发任务）
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
# 导入Rich库中的进度条相关组件
from rich.console import Console  # 用于在终端打印Rich格式化文本
from concurrent.futures import ThreadPoolExecutor  # 可用于线程池（本示例未使用线程池）

# 创建一个Rich控制台实例，用于打印带格式的输出
console = Console()

def rich_multiple_progress_example():
    """使用Rich库创建多行进度条示例"""
    console.print("[bold blue]使用Rich库的多行进度条示例[/bold blue]")  # 打印标题，蓝色加粗

    # 使用Progress上下文管理器创建一个进度条容器
    with Progress(
            SpinnerColumn(),  # 添加旋转动画列，显示任务正在进行
            TextColumn("[progress.description]{task.description}"),  # 显示任务描述
            BarColumn(),  # 显示进度条
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # 显示百分比进度
            TimeRemainingColumn(),  # 显示预计剩余时间
    ) as progress:

        # 添加三个不同的任务，每个任务都有总进度值total
        task1 = progress.add_task("下载数据...", total=100)
        task2 = progress.add_task("处理图片...", total=80)
        task3 = progress.add_task("生成报告...", total=60)

        # 使用循环模拟任务进度更新，直到所有任务完成
        while not progress.finished:
            # 如果任务未完成，则增加进度
            if not progress.tasks[task1].finished:
                progress.update(task1, advance=2)  # task1每次增加2单位进度

            if not progress.tasks[task2].finished:
                progress.update(task2, advance=1)  # task2每次增加1单位进度

            if not progress.tasks[task3].finished:
                progress.update(task3, advance=1.5)  # task3每次增加1.5单位进度

            time.sleep(0.1)  # 模拟任务执行间隔

def rich_nested_progress_example():
    """Rich库嵌套进度条示例"""
    console.print("\n[bold green]Rich嵌套进度条示例[/bold green]")  # 打印绿色标题

    # 创建进度条容器
    with Progress() as progress:
        # 添加总任务，用于表示整体进度
        overall_task = progress.add_task("整体进度", total=3)

        # 模拟三个阶段的任务
        for i, phase in enumerate(["初始化", "执行", "清理"], 1):
            progress.update(overall_task, description=f"阶段 {i}: {phase}")  # 更新总任务描述

            # 为每个阶段创建子任务
            subtask = progress.add_task(f"  {phase}步骤", total=20)

            # 更新子任务进度
            for j in range(20):
                time.sleep(0.05)  # 模拟执行时间
                progress.update(subtask, advance=1)  # 每次进度+1

            # 子任务完成后，从进度条中移除
            progress.remove_task(subtask)
            # 更新总任务进度
            progress.update(overall_task, advance=1)

def rich_custom_columns_example():
    """自定义列的Rich进度条示例"""
    console.print("\n[bold magenta]自定义列的Rich进度条[/bold magenta]")  # 打印标题

    # 自定义进度条显示的列，包括文件名、进度条、百分比、速度和剩余时间
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),  # 显示文件名
        BarColumn(bar_width=None),  # 显示进度条
        "[progress.percentage]{task.percentage:>3.1f}%",  # 百分比
        "•",  # 分隔符
        TextColumn("[bold green]{task.fields[speed]}"),  # 当前速度
        "•",  # 分隔符
        TimeRemainingColumn(),  # 剩余时间
    )

    with progress:
        # 模拟多个文件下载任务
        files = [
            {"name": "video.mp4", "size": 1000, "speed": "2.1 MB/s"},
            {"name": "audio.wav", "size": 500, "speed": "1.8 MB/s"},
            {"name": "data.zip", "size": 800, "speed": "3.2 MB/s"}
        ]

        tasks = []
        # 为每个文件添加任务，并设置自定义字段filename和speed
        for file_info in files:
            task = progress.add_task(
                "download",
                filename=file_info["name"],
                speed=file_info["speed"],
                total=file_info["size"]
            )
            tasks.append(task)

        # 模拟文件下载进度更新
        while not progress.finished:
            for i, task in enumerate(tasks):
                if not progress.tasks[task].finished:
                    progress.update(task, advance=10)  # 增加进度
                    # 动态更新速度信息
                    current_speed = f"{2.0 + i * 0.5:.1f} MB/s"
                    progress.update(task, speed=current_speed)

            time.sleep(0.1)  # 模拟下载延迟

# 程序入口
if __name__ == "__main__":
    rich_multiple_progress_example()  # 多行进度条示例
    # rich_nested_progress_example()    # 嵌套进度条示例
    # rich_custom_columns_example()     # 自定义列进度条示例

    console.print("\n[bold cyan]所有Rich示例完成！[/bold cyan]")  # 打印完成提示
