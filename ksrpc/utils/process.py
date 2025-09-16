import multiprocessing
import os
import signal
import subprocess

import select


def callback(process_name, stream_type, line):
    # 根据流类型添加不同前缀
    if stream_type == "stderr":
        print(f"[ERROR] {process_name}: {line}")
    else:
        print(f"[INFO] {process_name}: {line}")


def run_command(args, callback=callback):
    process_name = multiprocessing.current_process().name

    try:
        # 使用 subprocess 运行外部命令
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # 实时输出日志
        while process.poll() is None:
            # 检查 stdout/stderr 是否有数据
            rlist, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
            for stream in rlist:
                line = stream.readline()
                if line:
                    # 判断是 stdout 还是 stderr
                    if stream is process.stdout:
                        stream_type = "stdout"
                    elif stream is process.stderr:
                        stream_type = "stderr"
                    else:
                        stream_type = "unknown"

                    callback(process_name, stream_type, line.strip())

        # 等待进程结束
        process.wait()
    except KeyboardInterrupt:
        print(args, "已中断")
    except Exception as e:
        print(args, "已失败: ", e)
    finally:
        print(args, "已结束")


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
            if p.is_alive():
                print(f"Terminating {p.name} (PID: {p.pid})")
                p.terminate()  # 发送SIGTERM
                p.join(timeout=5)  # 等待5秒
                if p.is_alive():
                    print(f"Force killing {p.name} (PID: {p.pid})")
                    os.kill(p.pid, signal.SIGKILL)  # 强制终止
                    p.join()
        print("All processes terminated")
        return False  # 不抑制异常
