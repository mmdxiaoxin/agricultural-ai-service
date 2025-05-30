# 农业AI服务系统

这是一个基于Python的农业AI服务系统，集成了多种AI模型和功能，用于农业相关的智能诊断。系统采用现代化的技术栈，提供高性能、可扩展的AI服务能力。

## 功能特点

- 基于Flask的Web服务
  - RESTful API设计
  - 异步任务处理
  - 请求限流和超时控制
  - 跨域资源共享(CORS)支持
- Celery异步任务处理
  - 分布式任务队列
  - 任务状态监控
  - 失败任务重试机制
- 支持多种AI模型集成
  - PyTorch模型支持
  - ONNX模型部署和推理
  - 模型版本管理
  - 模型热更新
- 完整的系统功能
  - 用户认证和授权
  - 完整的日志系统
  - 系统监控和告警
  - 数据持久化存储
  - 文件上传和管理
- 开发友好
  - 详细的API文档
  - 完整的错误处理
  - 开发环境配置
  - 测试用例支持

## 系统要求

### 硬件要求
- CPU: 4核心及以上
- 内存: 8GB及以上
- 存储: 50GB可用空间
- GPU: NVIDIA GPU（可选，用于加速）

### 软件要求
- 操作系统
  - Windows 10/11
  - Ubuntu 20.04/22.04
  - CentOS 7/8
- Python 3.8+
- Redis 6.0+
- CUDA 11.8+（GPU加速需要）
- Docker 20.10+（容器化部署需要）
- NVIDIA Container Toolkit（GPU支持需要）

## 快速开始

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

5. 创建必要的目录
```bash
mkdir -p data weight uploads logs
```

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

2. 构建和运行容器
```bash
# 构建镜像
docker build -t agricultural-ai-service .

# 运行容器
docker run -d \
  --name agricultural-ai-service \
  --gpus all \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/weight:/app/weight \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  agricultural-ai-service
```

3. 使用Docker Compose（推荐）
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

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
# 使用waitress作为WSGI服务器
waitress-serve --host=0.0.0.0 --port=5000 app:app

# 使用gunicorn作为WSGI服务器（Linux）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

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

## 项目结构

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

## 配置说明

### 服务器配置
- CPU核心数：自动计算最佳线程数
- 内存使用：根据可用内存调整连接限制
- 请求超时：可配置的请求处理超时时间
- 文件上传：支持大文件上传和断点续传

### 模型配置
- 模型加载：支持动态加载和热更新
- 推理加速：支持GPU加速和批处理
- 内存管理：自动内存回收和优化

### 日志配置
- 日志级别：可配置的日志级别
- 日志轮转：自动日志轮转和清理
- 错误追踪：详细的错误堆栈信息

## 开发指南

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

3. 性能测试
```bash
python -m pytest tests/performance/
```

## 常见问题

### 1. 环境问题
- Q: 如何解决CUDA相关错误？
  A: 确保已正确安装CUDA和cuDNN，并设置正确的环境变量

- Q: Redis连接失败怎么办？
  A: 检查Redis服务是否启动，以及连接配置是否正确

### 2. 部署问题
- Q: 如何修改服务端口？
  A: 在`.env`文件中修改PORT配置，或使用环境变量覆盖

- Q: 如何配置HTTPS？
  A: 使用Nginx反向代理，并配置SSL证书

### 3. 性能问题
- Q: 如何提高推理速度？
  A: 使用GPU加速，启用批处理，优化模型结构

- Q: 如何处理内存泄漏？
  A: 定期检查内存使用情况，及时释放不需要的资源

## 维护说明

### 1. 日常维护
- 定期检查日志文件
- 监控系统资源使用情况
- 备份重要数据
- 更新依赖包

### 2. 故障处理
- 检查服务状态
- 查看错误日志
- 重启相关服务
- 恢复数据备份

### 3. 性能优化
- 优化数据库查询
- 使用缓存加速
- 调整服务器参数
- 优化模型结构

## 许可证

本项目采用 GNU Affero General Public License v3.0 许可证。

### 许可证说明

- 本项目是自由软件，您可以自由地分发和修改它
- 您可以自由地使用、修改和分发本软件
- 如果您修改了本软件，您必须将修改后的源代码公开
- 如果您通过网络提供服务，您必须向用户提供源代码
- 本软件不提供任何明示或暗示的保证

### 许可证要求

1. 源代码公开
   - 如果您修改了代码，必须公开修改后的源代码
   - 如果通过网络提供服务，必须向用户提供源代码

2. 版权声明
   - 必须保留原始版权声明
   - 必须包含许可证文本

3. 专利授权
   - 贡献者授予您使用其专利的权利
   - 您不得对下游用户施加额外的专利限制

4. 免责声明
   - 本软件按"原样"提供，不提供任何保证
   - 作者不对任何损失负责

### 如何遵守许可证

1. 使用本软件时：
   - 保留所有版权声明
   - 包含完整的许可证文本
   - 说明您对代码的修改

2. 分发本软件时：
   - 提供源代码
   - 说明许可证要求
   - 提供修改说明（如果有）

3. 修改本软件时：
   - 明确标注您的修改
   - 使用相同的许可证
   - 提供修改说明

完整的许可证文本请查看 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目维护者：mmdxiaoxin
- 电子邮件：782446723@qq.com
- 项目地址：https://github.com/mmdxiaoxin/agricultural-ai-service.git
