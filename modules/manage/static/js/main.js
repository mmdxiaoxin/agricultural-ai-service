// API基础URL
const API_BASE_URL = '/manage/api';

// 获取模型列表
async function getModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/models`);
        const data = await response.json();
        if (data.code === 200) {
            return data;
        }
        throw new Error(data.message || '获取模型列表失败');
    } catch (error) {
        console.error('获取模型列表失败:', error);
        showError('获取模型列表失败');
        return { code: 500, data: { models: {} }, message: error.message };
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
async function deleteModel(versionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/models/version/${versionId}`, {
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

// 显示成功消息
function showSuccess(message) {
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

// 处理删除模型
async function handleDeleteModel(versionId) {
    if (confirm('确定要删除这个模型吗？此操作不可恢复。')) {
        const success = await deleteModel(versionId);
        if (success) {
            showSuccess('模型删除成功');
            // 删除成功后刷新列表
            await initModelList();
        }
    }
}

// 初始化模型列表
async function initModelList() {
    try {
        const response = await getModels();
        if (response.code !== 200) {
            throw new Error(response.message);
        }
        
        const models = response.data.models;
        const tbody = document.querySelector('#modelTable tbody');
        tbody.innerHTML = '';

        if (!models || Object.keys(models).length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td colspan="7" style="text-align: center;">暂无模型数据</td>';
            tbody.appendChild(tr);
            return;
        }

        // 遍历每个模型组
        for (const [modelName, versions] of Object.entries(models)) {
            versions.forEach(model => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${modelName}</td>
                    <td>${model.model_type}</td>
                    <td>${model.version}</td>
                    <td>${model.task_types.join(', ')}</td>
                    <td>${model.description}</td>
                    <td>${new Date(model.created_at).toLocaleString()}</td>
                    <td>
                        <button onclick="handleDeleteModel(${model.version_id})">删除</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('初始化模型列表失败:', error);
        showError('初始化模型列表失败: ' + error.message);
        const tbody = document.querySelector('#modelTable tbody');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: red;">加载模型列表失败</td></tr>';
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