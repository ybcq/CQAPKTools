/**
 * CQApkTools 5.0 Web 应用前端脚本
 */

let logSubscriber = null;
let maxLogLines = 1000;
let successModal = null;

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', function() {
    connectSSE();
    bindActionButtons();
    // 初始化成功模态框
    const successModalEl = document.getElementById('successModal');
    if (successModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        successModal = new bootstrap.Modal(successModalEl);
    }
});

// ========== 日志面板折叠 ==========
function toggleLogPanel() {
    const panel = document.getElementById('logPanel');
    const btnIcon = document.querySelector('#logToggleBtn i');
    if (!panel || !btnIcon) return;

    const isCollapsed = panel.classList.toggle('collapsed');
    btnIcon.className = isCollapsed ? 'bi bi-chevron-double-left' : 'bi bi-chevron-double-right';
}

// ========== SSE 日志流 ==========
function connectSSE() {
    const evtSource = new EventSource('/api/logs');
    
    evtSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.msg) {
                appendLog(data.msg);
            }
        } catch (e) {
            // keep-alive 或解析失败
        }
    };

    evtSource.onerror = function() {
        appendLog('日志连接已断开，尝试重连...');
        setTimeout(connectSSE, 3000);
    };
}

function appendLog(msg) {
    const logContent = document.getElementById('logContent');
    if (!logContent) return;
    
    const line = document.createElement('div');
    line.className = 'log-line';
    line.textContent = msg;
    logContent.appendChild(line);

    // 限制日志条数
    while (logContent.children.length > maxLogLines) {
        logContent.removeChild(logContent.firstChild);
    }

    // 自动滚动到底部
    logContent.scrollTop = logContent.scrollHeight;
}

function clearLogs() {
    const logContent = document.getElementById('logContent');
    if (logContent) {
        logContent.innerHTML = '<div class="log-line">日志已清空</div>';
    }
}

// ========== 动作按钮绑定 ==========
function bindActionButtons() {
    // 所有带 data-action 的按钮
    document.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const action = this.getAttribute('data-action');
            
            switch (action) {
                case 'freeze_app':
                case 'unfreeze_app':
                case 'uninstall_app':
                    handleFreezeAction(this);
                    break;
                case 'one_key_batch':
                    handleOneKeyBatch(this);
                    break;
                case 'one_key_list':
                    handleOneKeyList(this);
                    break;
                case 'get_top_package':
                    getTopPackage();
                    break;
                case 'set_animation':
                    handleSetAnimation(this);
                    break;
                case 'set_background':
                    handleSetBackground(this);
                    break;
                case 'set_freezer':
                    handleSetFreezer(this);
                    break;
                case 'organize_folder':
                case 'process_apk_folder':
                    handleFolderAction(this);
                    break;
                case 'activate_app':
                    handleActivateApp(this);
                    break;
                case 'map_shared_disk':
                case 'unmap_shared_disk':
                case 'set_autorun_registry':
                case 'create_network_icon':
                    doAction(action, {});
                    break;
                case 'open_url':
                    const url = this.getAttribute('data-url');
                    if (url) window.open(url, '_blank');
                    break;
                case 'kill_engine':
                    handleKillEngine();
                    break;
                case 'launch_apkinstaller':
                    handleLaunchApkInstaller();
                    break;
                case 'start_rename':
                    handleStartRename();
                    break;
                case 'save_pattern':
                    handleSavePattern(this);
                    break;
                case 'register_context_menu':
                case 'unregister_context_menu':
                    handleContextMenu(action);
                    break;
                case 'start_extract':
                    handleStartExtract();
                    break;
                case 'batch_install':
                    handleBatchInstall(this);
                    break;
                case 'browse_file':
                    await handleBrowseFile(this);
                    break;
                case 'browse_folder':
                    await handleBrowseFolder(this);
                    break;
                default:
                    doAction(action, {});
            }
        });
    });

    // 连接设备按钮
    const connectBtn = document.getElementById('btn-connect-device');
    if (connectBtn) {
        connectBtn.addEventListener('click', connectDevice);
    }
}

// ========== 通用动作接口 ==========
async function doAction(action, params) {
    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action, params})
        });
        const data = await res.json();
        if (data.ok) {
                        showSuccessModal(data.msg);
        } else {
            showErrorModal('操作失败', data.msg);
        }
    } catch (e) {
        showErrorModal('网络错误', e.message);
    }
}

// ========== 文件/文件夹选择 ==========
async function handleBrowseFile(btn) {
    const title = btn.getAttribute('data-title') || '选择文件';
    const filter = btn.getAttribute('data-filter') || '';
    try {
        const res = await fetch(`/api/pick-file?title=${encodeURIComponent(title)}&filter=${encodeURIComponent(filter)}`);
        const data = await res.json();
        if (data.ok && data.data) {
            document.getElementById(btn.getAttribute('data-target')).value = data.data.path;
        } else {
            showErrorModal('提示', data.msg || '未选择文件');
        }
    } catch (e) {
        showErrorModal('网络错误', e.message);
    }
}

async function handleBrowseFolder(btn) {
    const title = btn.getAttribute('data-title') || '选择文件夹';
    try {
        const res = await fetch(`/api/pick-folder?title=${encodeURIComponent(title)}`);
        const data = await res.json();
        if (data.ok && data.data) {
            document.getElementById(btn.getAttribute('data-target')).value = data.data.path;
        } else {
            showErrorModal('提示', data.msg || '未选择文件夹');
        }
    } catch (e) {
        showErrorModal('网络错误', e.message);
    }
}

// ========== 澎湃冻结相关 ==========
async function handleFreezeAction(btn) {
    const pkg = btn.getAttribute('data-package');
    const useInput = btn.getAttribute('data-use-input');
    const keep = btn.getAttribute('data-keep') === '1';
    
    let packageName = pkg;
    if (useInput === '1') {
        packageName = document.getElementById('freeze-package-input').value.trim();
    }
    
    if (!packageName) {
        showErrorModal('提示', '请输入包名');
        return;
    }

    const action = btn.getAttribute('data-action');
    const endpoint = action === 'freeze_app' ? 'freeze_app' : 
                     action === 'unfreeze_app' ? 'unfreeze_app' : 'uninstall_app';
    const params = {package: packageName};
    if (action === 'uninstall_app') params.keep_data = keep;
    
    await doAction(endpoint, params);
}

async function handleOneKeyBatch(btn) {
    const type = btn.getAttribute('data-type');
    // 从页面获取预定义包名列表（排除电量与性能）
    const packages = [
        'com.miui.analytics', 'com.miui.systemAdSolution', 'com.xiaomi.joyose',
        'com.android.stk', 'com.miui.newhome', 'com.miui.hybrid', 'com.android.updater'
    ];
    
    await doAction('one_key_batch', {type, packages});
}

async function handleOneKeyList(btn) {
    const type = btn.getAttribute('data-type');
    const filePath = document.getElementById('freeze-filelist').value;
    
    if (!filePath) {
        showErrorModal('提示', '请选择CSV文件');
        return;
    }
    
    await doAction('one_key_list', {type, file_path: filePath});
}

async function getTopPackage() {
    const res = await fetch('/api/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'get_top_package', params: {}})
    });
    const data = await res.json();
    if (data.ok) {
        document.getElementById('freeze-package-input').value = data.data.package || '';
    }
}

// ========== 通用优化相关 ==========
async function handleSetAnimation(btn) {
    const useInputs = btn.getAttribute('data-use-inputs');
    let s1, s2, s3;
    
    if (useInputs === '1') {
        s1 = document.getElementById('anim-speed1').value;
        s2 = document.getElementById('anim-speed2').value;
        s3 = document.getElementById('anim-speed3').value;
    } else {
        s1 = btn.getAttribute('data-s1');
        s2 = btn.getAttribute('data-s2');
        s3 = btn.getAttribute('data-s3');
    }
    
    await doAction('set_animation', {speed1: s1, speed2: s2, speed3: s3});
}

async function handleSetBackground(btn) {
    const useInput = btn.getAttribute('data-use-input');
    let level;
    
    if (useInput === '1') {
        level = document.getElementById('bg-level').value;
    } else {
        level = btn.getAttribute('data-level');
    }
    
    await doAction('set_background', {level});
}

async function handleSetFreezer(btn) {
    const enable = btn.getAttribute('data-enable') === '1';
    await doAction('set_freezer', {enable});
}

async function handleFolderAction(btn) {
    const action = btn.getAttribute('data-action');
    const mode = btn.getAttribute('data-mode');
    const folderPath = document.getElementById('downgrade-folder').value;
    
    if (!folderPath) {
        showErrorModal('提示', '请选择文件夹');
        return;
    }
    
    const params = {folder_path: folderPath};
    if (mode) params.mode = mode;
    
    await doAction(action, params);
}

async function handleActivateApp(btn) {
    const appName = btn.getAttribute('data-app');
    await doAction('activate_app', {app_name: appName});
}

async function handleKillEngine() {
    await doAction('kill_engine', {});
}

async function handleLaunchApkInstaller() {
    await doAction('launch_apkinstaller', {});
}

// ========== 批量命名相关 ==========
async function handleStartRename() {
    const filePath = document.getElementById('rename-file').value;
    const folderPath = document.getElementById('rename-folder').value;
    
    if (!filePath && !folderPath) {
        showErrorModal('提示', '请选择文件或文件夹');
        return;
    }
    
    const params = {};
    if (filePath) params.file_path = filePath;
    if (folderPath) params.folder_path = folderPath;
    
    await doAction('start_rename', params);
}

async function handleSavePattern(btn) {
    const inputId = btn.getAttribute('data-use-input');
    const pattern = document.getElementById(inputId).value;
    
    await doAction('save_pattern', {pattern});
}

async function handleContextMenu(action) {
    await doAction(action, {});
}

// ========== 批量提取安装相关 ==========
async function handleStartExtract() {
    const extractPath = document.getElementById('extract-path').value;
    const deviceId = document.getElementById('device-id')?.value || '';
    
    if (!deviceId) {
        showErrorModal('提示', '请先连接设备');
        return;
    }
    
    if (!extractPath) {
        showErrorModal('提示', '请选择提取目录');
        return;
    }
    
    await doAction('start_extract', {
        device_id: deviceId,
        extract_path: extractPath
    });
}

async function handleBatchInstall(btn) {
    const mode = btn.getAttribute('data-mode');
    const installPath = document.getElementById('install-path').value;
    const keepData = document.getElementById('batch-keep-data').checked;
    const installIfNot = document.getElementById('batch-install-if-not').checked;
    
    if (!installPath) {
        showErrorModal('提示', '请选择安装目录');
        return;
    }
    
    await doAction('batch_install', {
        mode,
        install_path: installPath,
        keep_data: keepData,
        install_if_not_installed: installIfNot
    });
}

// ========== 设备连接 ==========
async function connectDevice() {
    const res = await fetch('/api/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'connect_device', params: {}})
    });
    const data = await res.json();
    const deviceId = document.getElementById('device-id');
    const statusText = document.getElementById('device-status-text');
    const statusBar = document.getElementById('device-status-bar');
    if (data.ok && data.data) {
        const status = data.data.status || '未连接';
        const connected = status === '已连接';
        if (deviceId) deviceId.value = data.data.device_id || '';
        if (statusText) statusText.textContent = status;
        if (statusBar) {
            statusBar.classList.toggle('connected', connected);
            statusBar.classList.toggle('disconnected', !connected);
        }
    } else {
        if (statusText) statusText.textContent = '未连接';
        if (statusBar) {
            statusBar.classList.remove('connected');
            statusBar.classList.add('disconnected');
        }
    }
}

// ========== 错误弹窗 ==========
function showErrorModal(title, message) {
    const modalTitle = document.getElementById('errorModalTitle');
    const modalBody = document.getElementById('errorModalBody');
    
    if (modalTitle) modalTitle.textContent = title || '提示';
    if (modalBody) modalBody.textContent = message || '';
    
    const modal = new bootstrap.Modal(document.getElementById('errorModal'));
    modal.show();
}

// ========== 成功弹窗 ==========
function showSuccessModal(message) {
    const msgEl = document.getElementById('successModalMessage');
    if (msgEl) msgEl.textContent = message;
    if (successModal) successModal.show();
}

