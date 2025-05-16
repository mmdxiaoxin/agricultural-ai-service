// 分片大小（5MB）
const CHUNK_SIZE = 5 * 1024 * 1024;

// 上传状态
let uploadTaskId = null;
let currentChunk = 0;
let totalChunks = 0;
let file = null;

// 获取DOM元素
const uploadForm = document.getElementById('uploadForm');
const progressBar = document.getElementById('uploadProgress');
const progressText = document.getElementById('progressText');
const submitButton = uploadForm.querySelector('button[type="submit"]');

// 创建上传任务
async function createUploadTask() {
    const formData = new FormData(uploadForm);
    formData.delete('model_file');  // 移除文件，因为我们要分片上传
    
    // 添加文件大小和分片数
    formData.append('total_size', file.size);
    formData.append('total_chunks', totalChunks);
    
    // 添加原始文件后缀名
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.') + 1);
    formData.append('original_extension', fileExtension);
    
    try {
        const response = await fetch('/manage/api/models/upload/create', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.code === 200) {
            return result.data.task_id;
        } else {
            throw new Error(result.message || '创建上传任务失败');
        }
    } catch (error) {
        throw new Error(`创建上传任务失败: ${error.message}`);
    }
}

// 上传分片
async function uploadChunk(chunkIndex, chunk) {
    const formData = new FormData();
    formData.append('task_id', uploadTaskId);
    formData.append('chunk_index', chunkIndex);
    formData.append('chunk', chunk);
    
    try {
        const response = await fetch('/manage/api/models/upload/chunk', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.code !== 200) {
            throw new Error(result.message || '上传分片失败');
        }
    } catch (error) {
        throw new Error(`上传分片失败: ${error.message}`);
    }
}

// 合并分片
async function mergeChunks() {
    const formData = new FormData();
    formData.append('task_id', uploadTaskId);
    
    try {
        const response = await fetch('/manage/api/models/upload/merge', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.code === 200) {
            return result;
        } else {
            throw new Error(result.message || '合并分片失败');
        }
    } catch (error) {
        throw new Error(`合并分片失败: ${error.message}`);
    }
}

// 更新进度条
function updateProgress(progress) {
    progressBar.style.width = `${progress}%`;
    progressText.textContent = `${Math.round(progress)}%`;
}

// 显示错误信息
function showError(message) {
    alert(`上传失败: ${message}`);
    console.error('上传错误:', message);
}

// 处理文件上传
async function handleFileUpload() {
    try {
        // 禁用提交按钮
        submitButton.disabled = true;
        
        // 获取文件
        file = document.getElementById('model_file').files[0];
        if (!file) {
            throw new Error('请选择要上传的文件');
        }
        
        // 验证文件类型
        const allowedExtensions = ['.pt', '.pth', '.onnx'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        if (!allowedExtensions.includes(fileExtension)) {
            throw new Error('不支持的文件类型，仅支持 .pt, .pth, .onnx 格式');
        }
        
        // 验证文件大小
        const maxSize = 500 * 1024 * 1024; // 500MB
        if (file.size > maxSize) {
            throw new Error('文件大小超过限制（最大500MB）');
        }
        
        // 计算分片数
        totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        
        // 创建上传任务
        uploadTaskId = await createUploadTask();
        
        // 上传分片
        for (let i = 0; i < totalChunks; i++) {
            const start = i * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);
            
            try {
                await uploadChunk(i, chunk);
                
                // 更新进度
                const progress = ((i + 1) / totalChunks) * 100;
                updateProgress(progress);
            } catch (error) {
                throw new Error(`上传第 ${i + 1} 个分片失败: ${error.message}`);
            }
        }
        
        // 合并分片
        const result = await mergeChunks();
        
        // 上传完成
        alert('模型上传成功！');
        window.location.href = '/manage/models';
        
    } catch (error) {
        showError(error.message);
    } finally {
        // 启用提交按钮
        submitButton.disabled = false;
    }
}

// 表单提交事件
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleFileUpload();
}); 