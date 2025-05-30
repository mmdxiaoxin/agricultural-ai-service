# 农业AI服务系统

这是一个基于Python的农业AI服务系统，集成了多种AI模型和功能，用于农业相关的智能诊断。

## 功能特点

- 基于Flask的Web服务
- Celery异步任务处理
- 支持多种AI模型集成
- 支持ONNX模型部署和推理
- 跨域支持
- 完整的日志系统
- 可配置的服务器参数
- 支持Windows和Linux环境
- RESTful API接口支持
- 基于JWT的接口认证

## 系统要求

- Python 3.8+
- Redis服务器
- CUDA支持（可选，用于GPU加速）
- ONNX Runtime（用于模型推理）

## API接口说明

系统提供两套API接口：

### 1. AI服务接口 (/ai)

这些接口用于提供AI服务，需要授权访问：

- 接口基础路径：`/ai`
- 认证方式：JWT Token
- 主要功能：
  - 图像识别和分析
  - 病害诊断
  - 作物生长状态评估
  - 产量预测
  - ONNX模型推理
  - 其他AI相关服务

使用示例：

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

### 2. 管理接口 (/manage)

这些接口用于系统管理，主要用于模型管理：

- 接口基础路径：`/manage`
- 认证方式：JWT Token
- 主要功能：
  - 模型创建和部署
  - 模型删除
  - 模型状态监控
  - 系统配置管理

使用示例：

```bash
# 创建新模型
curl -X POST http://localhost:5000/manage/models \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "new_model", "model_type": "detection"}'

# 删除模型
curl -X DELETE http://localhost:5000/manage/models/model_id \
  -H "Authorization: Bearer your_token"
```

## Docker部署

系统支持使用Docker进行部署，提供了完整的Docker配置：

### 使用Docker Compose部署（推荐）

1. 确保已安装Docker和Docker Compose
2. 确保已安装NVIDIA Container Toolkit（用于GPU支持）
3. 在项目根目录下运行：

```bash
docker-compose up -d
```

### 手动构建Docker镜像

1. 构建镜像：

```bash
docker build -t agricultural-ai-service .
```

2. 运行容器：

```bash
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

### Docker环境说明

- 使用CUDA 12.4作为基础镜像
- 包含所有必要的Python依赖
- 支持GPU加速
- 包含Redis服务
- 数据持久化存储
- 自动健康检查

### 注意事项

- 确保Docker主机有足够的GPU内存
- 首次运行时会下载较大的基础镜像
- 建议使用SSD存储以提高性能
- 定期备份数据卷中的数据

## 安装步骤

1. 克隆项目

```bash
git clone [项目地址]
cd agricultural-ai-service
```

2. 创建并激活虚拟环境（推荐）

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量
创建`.env`文件并配置必要的环境变量：

```env
FLASK_APP=app.py
FLASK_ENV=development
```

## 运行服务

系统支持三种运行模式：

1. 同时运行Web服务和Worker（默认）

```bash
python run.py
```

2. 仅运行Web服务

```bash
python run.py --mode web
```

3. 仅运行Worker

```bash
python run.py --mode worker
```

## 项目结构

```
agricultural-ai-service/
├── app.py              # 主应用入口
├── celery_app.py       # Celery配置
├── run.py             # 服务启动脚本
├── requirements.txt    # 项目依赖
├── config/            # 配置文件目录
├── common/            # 公共组件
├── modules/           # 功能模块
├── services/          # 服务层
├── data/             # 数据目录
├── weight/           # 模型权重
├── uploads/          # 上传文件目录
└── logs/             # 日志目录
```

## 配置说明

系统会自动根据服务器资源进行优化配置：

- CPU核心数：自动计算最佳线程数
- 内存使用：根据可用内存调整连接限制
- 请求超时：可配置的请求处理超时时间

## 开发说明

1. 添加新的AI模型：
   - 在`modules/ai`目录下创建新的模型处理模块
   - 在`services`目录下添加相应的服务层代码
   - 支持PyTorch模型转换为ONNX格式
   - 支持ONNX模型的部署和推理

2. 添加新的API端点：
   - 在`modules`目录下创建新的蓝图
   - 在`app.py`中注册新的蓝图

## 注意事项

- 确保Redis服务已启动
- 首次运行前检查配置文件
- 建议在生产环境中使用`waitress`作为WSGI服务器
- 注意定期清理`uploads`和`logs`目录
- 使用ONNX模型时确保已安装相应的运行时环境
- 对于GPU加速，确保安装了`onnxruntime-gpu`

## 许可证

[添加许可证信息]

## 联系方式

[添加联系方式]
