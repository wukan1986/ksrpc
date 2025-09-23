import multiprocessing
import subprocess
import sys
import threading
import time

import psutil


def callback(process_name, is_stderr, line, *args, **kwargs):
    # 根据流类型添加不同前缀
    if is_stderr:
        print(f"[ERROR] {process_name}: {line}", file=sys.stderr)
    else:
        print(f"[INFO] {process_name}: {line}", file=sys.stdout)


def run_command(cmds, callback, *args, **kwargs):
    """运行子程序

    TODO 目前我还没解决 print('\b')，只能整行确定后再打印
    """
    process_name = multiprocessing.current_process().name
    is_win = (sys.platform == 'win32')

    while True:
        # 子进程崩溃后可重启
        start_time = time.perf_counter()
        try:
            # 使用 subprocess 运行外部命令
            process = subprocess.Popen(
                cmds,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # universal_newlines=True,
            )
            print(cmds, f"启动子进程(PID:{process.pid})")

            # 定义从流中读取内容并调用回调函数的辅助函数
            def read_stream(stream, is_stderr):
                while True:
                    line = stream.readline()
                    if not line:  # 遇到EOF（通常是进程结束）
                        break
                    if is_win:
                        line = line.decode('gbk', errors='replace').strip()
                    else:
                        line = line.decode('utf-8', errors='replace').strip()

                    # 调用回调函数处理内容
                    callback(process_name, is_stderr, line.strip(), *args, **kwargs)

            # 为 stdout 和 stderr 创建单独的线程进行读取
            stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, False))
            stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, True))

            # 启动线程
            stdout_thread.start()
            stderr_thread.start()

            # 等待进程结束
            exit_code = process.wait()

            # 等待读取线程结束（确保所有输出都被处理）
            stdout_thread.join()
            stderr_thread.join()

            # 等待进程结束
            exit_code = process.wait()
            # 如果正常退出（退出码为0），则跳出循环
            if exit_code == 0:
                print(cmds, "子进程正常退出", exit_code)
                break
            else:
                print(cmds, "子进程异常退出", exit_code, file=sys.stderr)
        except KeyboardInterrupt:
            print(cmds, "已中断")
            break
        except Exception as e:
            print(cmds, "运行失败", e, file=sys.stderr)
        finally:
            print(cmds, "已结束")
            t = time.perf_counter() - start_time
            if t < 10:
                print(cmds, f"子进程启动后 {t:.3f} 秒退出。小于10秒，结束循环，等待人工处理", file=sys.stderr)
                break
            time.sleep(2)


def kill_subprocess(pid):
    # 清除子程序的功能
    parent = psutil.Process(pid)
    for p in parent.children():
        if not p.is_running():
            continue
        print(f"Terminating subprocess: {p.name()} (PID: {p.pid})")
        p.terminate()
        p.wait(timeout=5)

        if not p.is_running():
            continue
        print(f"Force killing subprocess: {p.name()} (PID: {p.pid})", file=sys.stderr)
        p.kill()
        p.wait()


def kill_process(p):
    # 清除程序的功能
    if not p.is_alive():
        return
    print(f"Terminating process: {p.name} (PID: {p.pid})")
    p.terminate()
    p.join(timeout=5)

    if not p.is_alive():
        return
    print(f"Force killing process: {p.name} (PID: {p.pid})", file=sys.stderr)
    p.kill()
    p.join()


class ProcessManager:
    def __init__(self, *processes):
        self.processes = processes

    def __enter__(self):
        for p in self.processes:
            p.start()
            print(f"Started process: {p.name} (PID: {p.pid})")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Terminating processes...")
        for p in self.processes:
            kill_subprocess(p.pid)
            kill_process(p)
        print("All processes terminated")
        return False  # 不抑制异常
