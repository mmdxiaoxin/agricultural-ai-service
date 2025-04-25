// API基础URL
const API_BASE_URL = '/manage/api';

// 获取模型列表
async function getModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/models`);
        const data = await response.json();
        if (data.code === 200) {
            return data.data;
        }
        throw new Error(data.message);
    } catch (error) {
        console.error('获取模型列表失败:', error);
        showError('获取模型列表失败');
        return [];
    }
}

// 获取模型详情
async function getModel(modelId) {
    try {
        const response = await fetch(`${API_BASE_URL}/models/${modelId}`);
        const data = await response.json();
        if (data.code === 200) {
            return data.data;
        }
        throw new Error(data.message);
    } catch (error) {
        console.error('获取模型详情失败:', error);
        showError('获取模型详情失败');
        return null;
    }
}

// 创建模型
async function createModel(modelData) {
    try {
        const response = await fetch(`${API_BASE_URL}/models`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(modelData),
        });
        const data = await response.json();
        if (data.code === 200) {
            return data.data;
        }
        throw new Error(data.message);
    } catch (error) {
        console.error('创建模型失败:', error);
        showError('创建模型失败');
        return null;
    }
}

// 更新模型
async function updateModel(modelId, modelData) {
    try {
        const response = await fetch(`${API_BASE_URL}/models/${modelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(modelData),
        });
        const data = await response.json();
        if (data.code === 200) {
            return data.data;
        }
        throw new Error(data.message);
    } catch (error) {
        console.error('更新模型失败:', error);
        showError('更新模型失败');
        return null;
    }
}

// 删除模型
async function deleteModel(modelId) {
    try {
        const response = await fetch(`${API_BASE_URL}/models/${modelId}`, {
            method: 'DELETE',
        });
        const data = await response.json();
        if (data.code === 200) {
            return true;
        }
        throw new Error(data.message);
    } catch (error) {
        console.error('删除模型失败:', error);
        showError('删除模型失败');
        return false;
    }
}

// 显示错误消息
function showError(message) {
    // 这里可以添加一个toast或者alert来显示错误消息
    alert(message);
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 根据当前页面执行相应的初始化操作
    const path = window.location.pathname;
    
    if (path === '/manage/models') {
        // 初始化模型列表页
        initModelList();
    } else if (path.startsWith('/manage/models/') && !path.endsWith('/create')) {
        // 初始化模型详情页
        const modelId = path.split('/').pop();
        initModelDetail(modelId);
    }
});

// 初始化模型列表页
async function initModelList() {
    const models = await getModels();
    const tableBody = document.querySelector('#modelTable tbody');
    
    if (tableBody) {
        tableBody.innerHTML = models.map(model => `
            <tr>
                <td>${model.name}</td>
                <td>${model.version}</td>
                <td>${model.task_type}</td>
                <td>
                    <a href="/manage/models/${model.id}" class="btn">查看</a>
                    <a href="/manage/models/${model.id}/edit" class="btn">编辑</a>
                    <button onclick="deleteModel(${model.id})" class="btn btn-danger">删除</button>
                </td>
            </tr>
        `).join('');
    }
}

// 初始化模型详情页
async function initModelDetail(modelId) {
    const model = await getModel(modelId);
    if (model) {
        // 更新页面内容
        document.querySelector('#modelName').textContent = model.name;
        document.querySelector('#modelVersion').textContent = model.version;
        document.querySelector('#modelType').textContent = model.task_type;
        // 其他模型信息...
    }
} 