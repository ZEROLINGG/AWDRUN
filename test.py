import time
import threading
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    Progress,
    TaskID,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    SpinnerColumn
)
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.live import Live
from rich import box
import keyboard
import sys

class ComplexTerminal:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.running = True
        self.user_input = ""
        self.current_option = 0
        self.options = ["开始任务", "暂停任务", "重置进度", "查看详情", "退出程序"]

        # 进度条相关
        self.progress = None
        self.main_task_id = None
        self.sub_task_id = None
        self.spinner_task_id = None
        self.counter = 0
        self.task_paused = False

        # 设置布局
        self.setup_layout()
        self.setup_progress()

    def setup_layout(self):
        """设置终端布局"""
        self.layout.split_column(
            Layout(name="header", size=5),      # 艺术字和摘要
            Layout(name="progress", size=10),   # 进度条区域
            Layout(name="control", minimum_size=8)  # 控制区域
        )

    def setup_progress(self):
        """设置进度条"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[name]}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=self.console
        )

        # 添加不同类型的任务
        self.main_task_id = self.progress.add_task(
            "主任务",
            name="总进度",
            total=100
        )

        self.sub_task_id = self.progress.add_task(
            "子任务",
            name="处理文件",
            total=50
        )

        self.spinner_task_id = self.progress.add_task(
            "后台任务",
            name="监控系统",
            total=None  # 无限进度条（旋转器）
        )

    def create_header(self):
        """创建顶部艺术字和摘要"""
        art_text = Text()
        art_text.append("╔═══════════════════════════════════╗\n║              AWDRUN               ║\n╚═══════════════════════════════════╝", style="cyan bold")
        status = "暂停中" if self.task_paused else "运行中"
        status_style = "yellow" if self.task_paused else "green"
        summary = Text(f"本次运行摘要: 已处理 {self.counter} 个项目 | 状态: {status}", style=status_style)

        header_content = Text()
        header_content.append(art_text)
        header_content.append("\n")
        header_content.append(summary)

        return Panel(
            Align.center(header_content),
            box=box.DOUBLE,
            style="bright_blue"
        )

    def create_progress_panel(self):
        """创建进度条面板"""
        # 创建计数器统计表格
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column("Metric", style="cyan", width=12)
        stats_table.add_column("Value", style="yellow", justify="right", width=8)

        stats_table.add_row("总计数:", str(self.counter))
        stats_table.add_row("成功:", str(max(0, self.counter - self.counter // 10)))
        stats_table.add_row("失败:", str(self.counter // 10))
        stats_table.add_row("成功率:", f"{max(0, 100 - self.counter // 10 * 10)}%")

        # 将进度条和统计表格组合
        progress_layout = Layout()
        progress_layout.split_row(
            Layout(Panel(self.progress, title="[bold yellow]任务进度[/bold yellow]", border_style="yellow"), ratio=2),
            Layout(Panel(stats_table, title="[bold cyan]统计信息[/bold cyan]", border_style="cyan"), ratio=1)
        )

        return progress_layout

    def create_control_panel(self):
        """创建控制面板"""
        # 操作选项
        options_text = Text("操作选项:\n", style="bold white")
        for i, option in enumerate(self.options):
            prefix = "► " if i == self.current_option else "  "
            style = "black on white" if i == self.current_option else "white"
            options_text.append(f"{prefix}{i+1}. {option}\n", style=style)

        # 操作提示
        help_text = Text("\n操作提示:\n", style="bold cyan")
        help_text.append("↑/↓ - 选择选项 | Enter/Space - 确认 | Esc - 退出 | R - 重置\n", style="dim white")

        # 状态信息
        task_status = "暂停" if self.task_paused else "运行"
        status_style = "yellow" if self.task_paused else "green"
        status_text = Text(f"\n任务状态: ", style="white")
        status_text.append(task_status, style=status_style)

        # 当前输入
        input_text = Text(f"\n输入信息: {self.user_input}", style="yellow")

        control_content = Text()
        control_content.append(options_text)
        control_content.append(help_text)
        control_content.append(status_text)
        control_content.append(input_text)

        return Panel(
            control_content,
            title="[bold red]终端控制[/bold red]",
            border_style="red"
        )

    def update_display(self):
        """更新显示内容"""
        self.layout["header"].update(self.create_header())
        self.layout["progress"].update(self.create_progress_panel())
        self.layout["control"].update(self.create_control_panel())

    def handle_input(self):
        """处理用户输入（在单独线程中运行）"""
        while self.running:
            try:
                if keyboard.is_pressed('up'):
                    self.current_option = (self.current_option - 1) % len(self.options)
                    time.sleep(0.2)
                elif keyboard.is_pressed('down'):
                    self.current_option = (self.current_option + 1) % len(self.options)
                    time.sleep(0.2)
                elif keyboard.is_pressed('enter') or keyboard.is_pressed('space'):
                    self.execute_option()
                    time.sleep(0.2)
                elif keyboard.is_pressed('esc'):
                    self.running = False
                    break
                elif keyboard.is_pressed('r'):
                    self.reset_progress()
                    time.sleep(0.2)
            except:
                # 处理键盘监听异常
                pass
            time.sleep(0.1)

    def execute_option(self):
        """执行选中的选项"""
        option = self.options[self.current_option]
        if option == "开始任务":
            self.task_paused = False
            self.user_input = "任务已启动"
            # 手动推进进度
            if self.counter < 100:
                self.counter += 5
                self.update_progress()

        elif option == "暂停任务":
            self.task_paused = True
            self.user_input = "任务已暂停"

        elif option == "重置进度":
            self.reset_progress()
            self.user_input = "进度已重置"

        elif option == "查看详情":
            main_progress = self.progress.tasks[0].percentage
            sub_progress = self.progress.tasks[1].percentage
            self.user_input = f"主任务: {main_progress:.1f}%, 子任务: {sub_progress:.1f}%"

        elif option == "退出程序":
            self.running = False

    def reset_progress(self):
        """重置所有进度"""
        self.counter = 0
        self.task_paused = False
        self.progress.reset(self.main_task_id)
        self.progress.reset(self.sub_task_id)

    def update_progress(self):
        """更新进度条"""
        # 更新主任务进度（基于计数器）
        main_completed = min(self.counter, 100)
        self.progress.update(self.main_task_id, completed=main_completed)

        # 更新子任务进度（以不同速度）
        sub_completed = min(self.counter * 2, 50)
        self.progress.update(self.sub_task_id, completed=sub_completed)

        # 旋转器任务持续运行
        self.progress.advance(self.spinner_task_id)

    def auto_update_counter(self):
        """自动更新计数器（模拟后台任务）"""
        while self.running:
            time.sleep(1.5)  # 每1.5秒更新一次
            if self.running and not self.task_paused:
                if self.counter < 100:  # 防止无限增长
                    self.counter += 1
                    self.update_progress()

    def run(self):
        """运行主程序"""
        # 启动输入处理线程
        input_thread = threading.Thread(target=self.handle_input, daemon=True)
        input_thread.start()

        # 启动自动计数器线程
        counter_thread = threading.Thread(target=self.auto_update_counter, daemon=True)
        counter_thread.start()

        # 主显示循环
        try:
            with Live(self.layout, console=self.console, refresh_per_second=24) as live:
                while self.running:
                    self.update_display()
                    # 即使任务暂停，旋转器依然转动
                    if not self.task_paused:
                        self.progress.advance(self.spinner_task_id)
                    time.sleep(0.25)
        finally:
            self.console.print("\n[bold red]程序已退出，感谢使用！[/bold red]")

if __name__ == "__main__":
    try:
        # 检查终端支持
        console = Console()
        if not console.is_terminal:
            print("警告: 当前环境可能不完全支持富文本显示")

        terminal = ComplexTerminal()
        console.print("[bold green]启动复杂终端管理系统...[/bold green]")

        time.sleep(1)
        terminal.run()

    except KeyboardInterrupt:
        print("\n程序被用户中断 (Ctrl+C)")
    except ImportError as e:
        print(f"缺少依赖库: {e}")
        print("请运行: pip install rich keyboard")
    except Exception as e:
        print(f"程序出错: {e}")
        import traceback
        traceback.print_exc()