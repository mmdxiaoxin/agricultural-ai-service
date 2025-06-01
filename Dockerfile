# 使用NVIDIA CUDA基础镜像
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# 添加元数据标签
LABEL maintainer="Agricultural AI Service Team"
LABEL version="1.0"
LABEL description="Agricultural AI Service with CUDA support"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH} \
    PYTHONPATH=/app \
    PYTHONHASHSEED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=UTF-8

# 安装系统依赖和常用工具
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    wget \
    vim \
    htop \
    net-tools \
    procps \
    libcublas11 \
    libcublas-dev \
    libcublasLt11 \
    libcublasLt-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt environment.yml ./

# 创建并激活虚拟环境
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir ipython

# 验证CUDA和ONNX安装
RUN python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())" && \
    python3 -c "import onnxruntime; print('ONNX Runtime version:', onnxruntime.__version__)" && \
    python3 -c "import onnxruntime; print('ONNX Runtime GPU available:', 'GPU' in onnxruntime.get_available_providers())"

# 复制剩余项目文件
COPY . .

# 创建必要的目录并设置权限
RUN mkdir -p data weight uploads logs && \
    chmod -R 755 /app && \
    chown -R nobody:nogroup /app

# 暴露端口
EXPOSE 5000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 设置非root用户
USER nobody

# 启动命令
CMD ["python", "run.py"]
