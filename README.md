# 🌱 农业AI服务系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey.svg)
![ONNX](https://img.shields.io/badge/ONNX-1.12+-orange.svg)
![License](https://img.shields.io/badge/License-AGPL%20v3.0-green.svg)

一个基于Python的农业AI服务系统，集成了多种AI模型和功能，用于农业相关的智能诊断。系统采用现代化的技术栈，提供高性能、可扩展的AI服务能力。

[快速开始](#快速开始) | [功能特点](#功能特点) | [系统要求](#系统要求) | [部署指南](#项目部署) | [开发文档](#开发指南) | [常见问题](#常见问题)

</div>

## ✨ 功能特点

### 🚀 基于Flask的Web服务
- 📡 RESTful API设计
- ⚡ 异步任务处理
- 🛡️ 请求限流和超时控制
- 🌐 跨域资源共享(CORS)支持

### 🔄 Celery异步任务处理
- 📊 分布式任务队列
- 📈 任务状态监控
- 🔁 失败任务重试机制

### 🤖 支持多种AI模型集成
- 🧠 PyTorch模型支持
- ⚡ ONNX模型部署和推理
- 📦 模型版本管理
- 🔄 模型热更新

### 🛠️ 完整的系统功能
- 🔐 用户认证和授权
- 📝 完整的日志系统
- 📊 系统监控和告警
- 💾 数据持久化存储
- 📤 文件上传和管理

### 👨‍💻 开发友好
- 📚 详细的API文档
- 🐛 完整的错误处理
- ⚙️ 开发环境配置
- ✅ 测试用例支持

## 💻 系统要求

### 硬件要求
| 组件 | 要求 |
|------|------|
| CPU | 4核心及以上 |
| 内存 | 8GB及以上 |
| 存储 | 50GB可用空间 |
| GPU | NVIDIA GPU（可选，用于加速） |

### 软件要求
| 类型 | 要求 |
|------|------|
| 操作系统 | Windows 10/11, Ubuntu 20.04/22.04, CentOS 7/8 |
| Python | 3.8+ |
| Redis | 6.0+ |
| CUDA | 11.8+（GPU加速需要） |
| Docker | 20.10+（容器化部署需要） |
| NVIDIA Container Toolkit | （GPU支持需要） |

## 🚀 快速开始

### 1. 环境准备

#### Windows环境
```bash
# 安装Python
# 从 https://www.python.org/downloads/ 下载并安装Python 3.10

# 安装CUDA（如果需要GPU支持）
# 从 https://developer.nvidia.com/cuda-downloads 下载并安装CUDA 12.4

# 安装Redis
# 从 https://github.com/microsoftarchive/redis/releases 下载并安装Redis
```

#### Linux环境
```bash
# 安装Python
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# 安装CUDA（如果需要GPU支持）
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda-repo-ubuntu2204-12-4-local_12.4.0-525.85.05-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-4-local_12.4.0-525.85.05-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-4-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda

# 安装Redis
sudo apt install redis-server
```

### 2. 项目部署

#### 方法一：直接部署

1. 克隆项目
```bash
git clone https://github.com/mmdxiaoxin/agricultural-ai-service.git
cd agricultural-ai-service
```

2. 创建虚拟环境
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖
```bash
# 使用conda安装（推荐）
conda env create -f environment.yml

# 或使用pip安装
pip install -r requirements.txt
```

4. 配置环境变量
创建`.env`文件：
```env
# 应用配置
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# 服务器配置
HOST=0.0.0.0
PORT=5000
WORKERS=4
SERVER_THREADS=8  # 服务器线程数，不设置则自动计算（CPU核心数 * 2，最大32）

# IP访问限制配置
ALLOWED_IPS=127.0.0.1,localhost,::1,172.17.0.1  # 允许模型管理模块界面访问的IP地址列表，用逗号分隔

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# 文件上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

5. 创建必要的目录（重要！）
```bash
# 创建数据目录
mkdir -p data/matplotlib  # 用于存储matplotlib配置
mkdir -p data/yolo       # 用于存储YOLO配置

# 创建模型权重目录
mkdir -p weight

# 创建上传文件目录
mkdir -p uploads/chunks  # 用于存储分片上传的临时文件

# 创建日志目录
mkdir -p logs

# 设置目录权限（Linux环境）
chmod -R 755 data weight uploads logs
```

> ⚠️ **重要提示**：在启动服务之前，必须确保以上所有目录都已创建，否则服务可能无法正常运行。特别是在Docker环境中，虽然docker-compose会自动创建挂载的目录，但建议在启动前手动检查这些目录是否存在。

#### 方法二：Docker部署

1. 安装Docker和Docker Compose
```bash
# Windows
# 从 https://www.docker.com/products/docker-desktop 下载并安装Docker Desktop

# Linux
curl -fsSL https://get.docker.com | sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. 使用Docker Compose启动服务
```bash
# 创建必要的目录
mkdir -p data/matplotlib data/yolo weight uploads/chunks logs

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

### Dockerfile说明

如果您需要自定义构建Docker镜像，可以使用项目中的Dockerfile。以下是Dockerfile的详细说明：

#### 基础镜像
```dockerfile
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04
```
- 使用NVIDIA官方CUDA 12.4.0运行时镜像
- 基于Ubuntu 22.04系统
- 包含CUDA运行时环境

#### 环境配置
```dockerfile
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}
```
- 设置Python输出不缓冲
- 配置时区为上海
- 配置CUDA环境变量
- 设置Python相关环境变量

#### 系统依赖
```dockerfile
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
    procps
```
- 安装Python 3.10
- 安装系统工具和依赖库
- 安装开发调试工具

#### Python环境
```dockerfile
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```
- 创建Python虚拟环境
- 配置pip使用阿里云镜像源
- 安装项目依赖

#### 验证和检查
```dockerfile
RUN python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())" && \
    python3 -c "import onnxruntime; print('ONNX Runtime version:', onnxruntime.__version__)"
```
- 验证CUDA可用性
- 验证ONNX Runtime安装
- 检查GPU支持状态

#### 安全配置
```dockerfile
RUN chmod -R 755 /app && \
    chown -R nobody:nogroup /app
USER nobody
```
- 设置适当的文件权限
- 使用非root用户运行服务
- 增强容器安全性

#### 健康检查
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
```
- 每30秒检查一次服务健康状态
- 超时时间30秒
- 启动后5秒开始检查
- 连续3次失败判定为不健康

#### 构建和运行
```bash
# 构建镜像
docker build -t agricultural-ai-service .

# 运行容器
docker run -d \
    --name agricultural-ai-service \
    --gpus all \
    -p 5001:5000 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/weight:/app/weight \
    -v $(pwd)/uploads:/app/uploads \
    -v $(pwd)/logs:/app/logs \
    agricultural-ai-service
```

> ⚠️ **注意**：
> 1. 虽然Docker会自动创建挂载的目录，但建议在启动前手动创建这些目录，以确保目录结构和权限正确。
> 2. 特别是`data/matplotlib`和`data/yolo`这样的子目录，需要手动创建。
> 3. Web服务和Celery Worker需要共享相同的卷挂载，以确保数据一致性。
> 4. 确保Redis服务已经启动并可访问，因为Celery Worker依赖Redis进行任务队列管理。

### 容器说明

#### Web 服务容器
- 运行 Flask Web 服务
- 暴露 5000 端口
- 包含健康检查端点
- 支持 GPU 加速
- 使用 Gunicorn 作为 WSGI 服务器（Linux环境）
- 使用 Waitress 作为 WSGI 服务器（Windows环境）

#### Celery Worker 容器
- 运行 Celery Worker 进程
- 支持 GPU 加速
- 包含 Celery 健康检查
- 自动重连 Redis
- 支持任务重试和错误处理
- 内存使用限制和自动回收

### 容器间通信
- Web 服务和 Celery Worker 通过 Redis 进行任务队列通信
- 共享相同的卷挂载，确保数据一致性
- 使用相同的环境变量配置
- 支持容器间的服务发现

### 3. 启动服务

#### 开发环境
```bash
# 启动所有服务
python run.py

# 仅启动Web服务
python run.py --mode web

# 仅启动Worker
python run.py --mode worker
```

#### 生产环境
```bash
# Windows环境手动启动（使用waitress作为WSGI服务器）
waitress-serve --host=0.0.0.0 --port=5000 app:app

# Linux环境手动启动（使用gunicorn作为WSGI服务器）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

> 💡 **注意**：`run.py` 会根据操作系统自动选择合适的 WSGI 服务器（Windows 使用 waitress，Linux 使用 gunicorn），并自动配置最优的服务器参数，不需要手动启动。

### 4. 验证部署

1. 检查服务状态
```bash
curl http://localhost:5000/health
```

2. 测试API接口
```bash
# 获取访问令牌
curl -X POST http://localhost:5000/ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# 调用AI服务
curl -X POST http://localhost:5000/ai/detect \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image"}'
```

## 📁 项目结构

```
agricultural-ai-service/
├── app.py              # 主应用入口
├── celery_app.py       # Celery配置
├── run.py             # 服务启动脚本
├── requirements.txt    # 项目依赖
├── environment.yml    # Conda环境配置
├── Dockerfile         # Docker构建文件
├── docker-compose.yml # Docker Compose配置
├── config/            # 配置文件目录
│   ├── __init__.py
│   └── app_config.py
├── common/            # 公共组件
│   ├── utils/        # 工具类
│   └── init/         # 初始化模块
├── modules/           # 功能模块
│   ├── ai/           # AI服务模块
│   ├── manage/       # 管理模块
│   └── health/       # 健康检查模块
├── services/          # 服务层
├── data/             # 数据目录
├── weight/           # 模型权重
├── uploads/          # 上传文件目录
└── logs/             # 日志目录
```

## ⚙️ 配置说明

### 配置文件结构
```
config/
├── __init__.py        # 配置包初始化文件
├── app_config.py      # 应用主配置
├── celery_config.py   # Celery任务队列配置
├── resnet_config.py   # ResNet模型配置
└── yolo_config.py     # YOLO模型配置
```

### 配置模块说明

#### 1. app_config.py
应用主配置文件，包含以下主要配置：
- 基础路径配置（日志、上传、模型权重等目录）
- 服务器配置（主机、端口、调试模式）
- CORS配置（跨域资源共享）
- JWT配置（认证相关）
- 请求配置（超时、文件大小限制）
- 日志配置（日志级别、格式、轮转）
- Redis配置（缓存和消息队列）
- IP访问限制配置
- 文件上传配置（分片上传、大小限制）

#### 2. celery_config.py
Celery任务队列配置，包含：
- Redis连接配置
- 任务序列化配置
- 工作进程配置
- 任务路由和队列配置
- 任务超时和重试配置
- 内存管理配置

#### 3. resnet_config.py
ResNet模型配置，包含：
- 支持的ResNet版本（18/34/50/101/152）
- 模型默认参数配置
- 设备配置（CPU/GPU）
- 图像预处理参数
- 模型结构参数

#### 4. yolo_config.py
YOLO模型配置，包含：
- 推理设备配置
- 检测参数（置信度、IoU阈值）
- 模型推理配置（半精度、NMS等）
- 最大检测框数量限制

### 环境变量配置
创建`.env`文件：
```env
# 应用配置
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# 服务器配置
HOST=0.0.0.0
PORT=5000
WORKERS=4
SERVER_THREADS=8  # 服务器线程数，不设置则自动计算（CPU核心数 * 2，最大32）

# IP访问限制配置
ALLOWED_IPS=127.0.0.1,localhost,::1,172.17.0.1  # 允许访问的IP地址列表，用逗号分隔

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# JWT配置
JWT_SECRET_KEY=your-secret-key # 注意要与平台服务端的JWT秘钥相同，否则无法通过签名
JWT_ACCESS_TOKEN_EXPIRES=3600

# 文件上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 配置最佳实践
1. 开发环境配置
   - 启用调试模式（FLASK_DEBUG=1）
   - 使用本地Redis
   - 设置较小的文件上传限制
   - 使用详细的日志级别

2. 生产环境配置
   - 禁用调试模式（FLASK_DEBUG=0）
   - 使用强密码的Redis
   - 根据服务器资源调整线程数
   - 使用适当的日志级别
   - 配置正确的CORS策略
   - 设置合理的IP访问限制

3. 模型配置建议
   - 根据硬件资源选择合适的模型版本
   - 调整推理参数以平衡性能和准确率
   - 监控内存使用情况
   - 定期更新模型权重

## 👨‍💻 开发指南

### 1. 添加新的AI模型
1. 在`modules/ai`目录下创建新的模型处理模块
2. 在`services`目录下添加相应的服务层代码
3. 支持PyTorch模型转换为ONNX格式
4. 支持ONNX模型的部署和推理

### 2. 添加新的API端点
1. 在`modules`目录下创建新的蓝图
2. 在`app.py`中注册新的蓝图
3. 实现相应的路由和视图函数
4. 添加请求参数验证和错误处理

### 3. 测试
1. 单元测试
```bash
python -m pytest tests/
```

2. 接口测试
```bash
python -m pytest tests/api/
```

## 🤔 常见问题

### 1. 环境问题
- Q: 如何解决CUDA相关错误？
  A: 确保已正确安装CUDA和cuDNN，并设置正确的环境变量

- Q: Redis连接失败怎么办？
  A: 检查Redis服务是否启动，以及连接配置是否正确

- Q: 为什么会出现"Cannot re-initialize CUDA in forked subprocess"错误？
  A: 这是因为在Linux系统中，Python多进程默认使用fork方式启动，而CUDA不支持fork方式。系统已经配置为使用spawn方式启动多进程，如果仍然遇到此错误，请确保：
  1. 使用最新版本的代码
  2. 在启动服务前清理所有Python进程
  3. 确保没有其他程序占用GPU资源

### 2. 部署问题
// ... existing code ...