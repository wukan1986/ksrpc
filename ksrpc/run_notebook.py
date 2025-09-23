import multiprocessing
import sys
import time
from typing import Dict, Any

from IPython.display import clear_output

from ksrpc.utils.process import run_command, ProcessManager


def callback(process_name, is_stderr, line, shared_time, shared_count, clear_count):
    # 使用控制台输出清屏，但异步发送数据时，进度条直接显示完成了。所以要多留一些空闲时间
    with shared_time.get_lock():
        shared_time.value = time.perf_counter()
    with shared_count.get_lock():
        i = shared_count.value + 1
        shared_count.value = i

    # 定义颜色代码
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"

    # 根据流类型设置颜色
    if is_stderr:
        color = RED
    else:
        color = GREEN

    # 创建带颜色的输出
    colored_line = f"{BOLD}{color}[{process_name}]{RESET}: {line}"

    # 每N条清屏一次
    if i % clear_count == 0:
        clear_output(wait=True)

    if is_stderr:
        print(line, file=sys.stderr)
    else:
        print(colored_line, file=sys.stdout)


def main(commands: Dict[str, Any], idle_timeout: int = 60 * 10, clear_count: int = 40):
    """

    Parameters
    ----------
    commands:
        命令
    idle_timeout: int
        空闲多少秒后停止服务。利用的控制台输出，发送大数据时，发送进度条已经走完，但数据还在发送中，过短可能导致服务中断
    clear_count: int
        输出多少行后清屏

    """
    print('注意：子进程模式下，通过管道获取标准输出，进度条是一次性打印', file=sys.stderr)
    # 创建共享变量 (使用'd'表示双精度浮点数)
    shared_time = multiprocessing.Value('d', time.perf_counter())
    shared_count = multiprocessing.Value('i', 0)

    processes = []
    for k, v in commands.items():
        p = multiprocessing.Process(target=run_command, name=k, args=(v, callback, shared_time, shared_count, clear_count))
        processes.append(p)

    try:
        print(f"!!!注意：空闲 {idle_timeout} 秒后，应用将退出!!!", file=sys.stderr)
        with ProcessManager(*processes):
            while True:
                current_time = time.perf_counter()
                # 读取共享变量值
                with shared_time.get_lock():
                    last_activity = shared_time.value

                print(f"最后活动时间: {last_activity:.0f}, "
                      f"当前时间: {current_time:.0f}, "
                      f"空闲时间: {current_time - last_activity:-3.0f}/{idle_timeout}")

                if current_time - last_activity > idle_timeout:
                    print("!!!空闲时间到，退出!!!", file=sys.stderr)
                    break
                time.sleep(15)
    except KeyboardInterrupt:
        print("主进程已中断")
    except Exception as e:
        print("主进程错误: ", e, file=sys.stderr)
    finally:
        print("结束服务")


if __name__ == '__main__':
    commands = {
        # "ksrpc": ["python", "-u", "-m", "ksrpc.run_app"],
        # "frpc": ["./frpc", "-c", "./frpc.toml"],
        "ksrpc": ["uv", "run", "python", "-u", "-m", "ksrpc.run_app", "--config", r"./config.py"],
    }
    main(commands, idle_timeout=300, clear_count=35)
