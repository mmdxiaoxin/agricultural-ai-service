import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class EnvConfig:
    """环境变量配置类"""

    @staticmethod
    def get_server_threads(cpu_count: int) -> int:
        """
        获取服务器线程数配置

        Args:
            cpu_count: CPU核心数

        Returns:
            int: 配置的线程数或自动计算的线程数
        """
        env_threads = os.getenv("SERVER_THREADS")
        if env_threads and env_threads.isdigit():
            return min(int(env_threads), 32)  # 限制最大32个线程
        return min(cpu_count * 2, 32)  # 每个核心2个线程，最大32个线程
