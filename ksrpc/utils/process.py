import multiprocessing
import subprocess
import sys
import time

import psutil
import select


def callback(process_name, is_stderr, line):
    # 根据流类型添加不同前缀
    if is_stderr:
        print(f"[ERROR] {process_name}: {line}", file=sys.stderr)
    else:
        print(f"[INFO] {process_name}: {line}", file=sys.stdout)


def run_command(args, callback):
    process_name = multiprocessing.current_process().name

    while True:
        # 子进程崩溃后可重启
        try:
            # 使用 subprocess 运行外部命令
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            print(args, f"启动子进程(PID:{process.pid})")

            # 实时输出日志
            while process.poll() is None:
                # 检查 stdout/stderr 是否有数据
                rlist, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                for stream in rlist:
                    line = stream.readline()
                    if line:
                        callback(process_name, stream == process.stderr, line.strip())

            # 等待进程结束
            exit_code = process.wait()
            # 如果正常退出（退出码为0），则跳出循环
            if exit_code == 0:
                print(args, "正常退出", exit_code)
                break
            else:
                print(args, "异常退出", exit_code)
        except KeyboardInterrupt:
            print(args, "已中断")
            break
        except Exception as e:
            print(args, "运行失败", e)
        finally:
            print(args, "已结束")
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
        print(f"Force killing subprocess: {p.name()} (PID: {p.pid})")
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
    print(f"Force killing process: {p.name} (PID: {p.pid})")
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
