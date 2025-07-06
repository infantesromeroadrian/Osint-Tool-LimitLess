// Variables globales para el sistema Tony Stark
let startTime = Date.now();
let queryCount = 0;
let systemOnline = true;

// Inicialización del sistema cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    initializeSystem();
    setupEventListeners();
    startSystemMonitoring();
});

// Inicialización del sistema
function initializeSystem() {
    console.log('🚀 LimitLess OSINT Tool - Tony Stark Interface Initializing...');
    
    // Verificar estado del sistema
    checkSystemStatus();
    
    // Agregar entrada al log de actividad
    addLogEntry('System online - All systems operational');
    
    // Animación de inicio del reactor Arc
    animateReactorStartup();
    
    console.log('✅ System initialized successfully');
}

// Configurar event listeners
function setupEventListeners() {
    // Botón de ejecutar
    const executeBtn = document.getElementById('executeBtn');
    executeBtn.addEventListener('click', executeCommand);
    
    // Input de comando (Enter para ejecutar)
    const commandInput = document.getElementById('commandInput');
    commandInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            executeCommand();
        }
    });
    
    // Botón de micrófono
    const micIcon = document.getElementById('micIcon');
    micIcon.addEventListener('click', toggleVoiceRecognition);
    
    // Botones de acciones rápidas
    const actionBtns = document.querySelectorAll('.action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            handleQuickAction(this.dataset.action);
        });
    });
    
    // Botón de limpiar resultados
    const clearBtn = document.getElementById('clearResults');
    clearBtn.addEventListener('click', clearResults);
    
    // Efectos de sonido al hacer hover en botones
    addHoverEffects();
}

// Verificar estado del sistema
async function checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'online') {
            updateSystemStatus(true);
            document.getElementById('aiStatus').textContent = 'GPT-4.1 ✓';
            document.getElementById('voiceStatus').textContent = 'WHISPER ✓';
        }
    } catch (error) {
        console.error('Error checking system status:', error);
        updateSystemStatus(false);
        addLogEntry('System check failed - Connection error');
    }
}

// Actualizar estado del sistema
function updateSystemStatus(online) {
    systemOnline = online;
    const statusLight = document.querySelector('.status-light');
    const statusText = document.querySelector('.status-text');
    
    if (online) {
        statusLight.classList.add('active');
        statusText.textContent = 'SYSTEM ONLINE';
    } else {
        statusLight.classList.remove('active');
        statusText.textContent = 'SYSTEM OFFLINE';
    }
}

// Iniciar monitoreo del sistema
function startSystemMonitoring() {
    // Actualizar uptime cada segundo
    setInterval(updateUptime, 1000);
    
    // Verificar estado del sistema cada 30 segundos
    setInterval(checkSystemStatus, 30000);
    
    // Animación de la barra de energía
    animatePowerBar();
}

// Actualizar tiempo de actividad
function updateUptime() {
    const now = Date.now();
    const uptime = now - startTime;
    const hours = Math.floor(uptime / 3600000);
    const minutes = Math.floor((uptime % 3600000) / 60000);
    const seconds = Math.floor((uptime % 60000) / 1000);
    
    const uptimeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('uptime').textContent = uptimeString;
}

// Ejecutar comando
async function executeCommand() {
    const commandInput = document.getElementById('commandInput');
    const command = commandInput.value.trim();
    
    if (!command) {
        showNotification('Please enter a command', 'warning');
        return;
    }
    
    if (!systemOnline) {
        showNotification('System offline - Cannot execute command', 'error');
        return;
    }
    
    // Mostrar loading
    showLoading(true);
    
    // Agregar al log
    addLogEntry(`Executing: ${command}`);
    
    // Incrementar contador
    queryCount++;
    document.getElementById('queryCount').textContent = queryCount;
    
    try {
        // Simular procesamiento
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Enviar comando al backend
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command: command,
                timestamp: new Date().toISOString()
            })
        });
        
        const data = await response.json();
        
        // Mostrar resultados
        displayResults(command, data);
        
        // Limpiar input
        commandInput.value = '';
        
        // Agregar al log
        addLogEntry(`Command executed successfully`);
        
    } catch (error) {
        console.error('Error executing command:', error);
        showNotification('Error executing command', 'error');
        addLogEntry(`Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Mostrar/ocultar loading
function showLoading(show) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Alternar reconocimiento de voz
function toggleVoiceRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showNotification('Voice recognition not supported in this browser', 'error');
        return;
    }
    
    const micIcon = document.getElementById('micIcon');
    
    if (micIcon.classList.contains('recording')) {
        // Detener grabación
        micIcon.classList.remove('recording');
        micIcon.style.color = '#00d4ff';
        addLogEntry('Voice recognition stopped');
    } else {
        // Iniciar grabación
        micIcon.classList.add('recording');
        micIcon.style.color = '#ffd700';
        addLogEntry('Voice recognition activated');
        
        // Simular reconocimiento de voz
        setTimeout(() => {
            micIcon.classList.remove('recording');
            micIcon.style.color = '#00d4ff';
            document.getElementById('commandInput').value = 'Voice command recognized';
            addLogEntry('Voice input processed');
        }, 3000);
    }
}

// Manejar acciones rápidas
function handleQuickAction(action) {
    const actionNames = {
        'image-analysis': 'Image Analysis',
        'social-search': 'Social Media Search',
        'domain-recon': 'Domain Reconnaissance',
        'transcript': 'Audio Transcription'
    };
    
    const actionName = actionNames[action] || action;
    addLogEntry(`Quick action: ${actionName}`);
    
    // Simular carga del módulo
    showLoading(true);
    
    setTimeout(() => {
        showLoading(false);
        showNotification(`${actionName} module loaded`, 'success');
        
        // Agregar placeholder en área de resultados
        const resultsContent = document.getElementById('resultsContent');
        resultsContent.innerHTML = `
            <div class="module-placeholder">
                <h4>${actionName.toUpperCase()}</h4>
                <p>Module loaded and ready for use.</p>
                <p>Use the command input to interact with this module.</p>
            </div>
        `;
    }, 1500);
}

// Mostrar resultados
function displayResults(command, data) {
    const resultsContent = document.getElementById('resultsContent');
    
    const resultHtml = `
        <div class="result-item">
            <div class="result-header">
                <h4>QUERY: ${command.toUpperCase()}</h4>
                <span class="result-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="result-content">
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = resultHtml;
}

// Limpiar resultados
function clearResults() {
    const resultsContent = document.getElementById('resultsContent');
    resultsContent.innerHTML = `
        <div class="no-results">
            <i class="fas fa-search"></i>
            <p>No analysis performed yet. Execute a query to see results.</p>
        </div>
    `;
    addLogEntry('Results cleared');
}

// Agregar entrada al log
function addLogEntry(message) {
    const activityLog = document.getElementById('activityLog');
    const time = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message">${message}</span>
    `;
    
    activityLog.insertBefore(logEntry, activityLog.firstChild);
    
    // Mantener solo los últimos 20 logs
    while (activityLog.children.length > 20) {
        activityLog.removeChild(activityLog.lastChild);
    }
}

// Mostrar notificación
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Agregar estilos dinámicos
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 17, 34, 0.9);
        border: 1px solid ${type === 'error' ? '#ff4444' : type === 'success' ? '#44ff44' : '#00d4ff'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1001;
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Orbitron', monospace;
        box-shadow: 0 0 20px ${type === 'error' ? '#ff4444' : type === 'success' ? '#44ff44' : '#00d4ff'};
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Animación de inicio del reactor
function animateReactorStartup() {
    const reactor = document.querySelector('.arc-reactor');
    reactor.style.animation = 'reactorStartup 3s ease-out';
}

// Animación de la barra de energía
function animatePowerBar() {
    const powerFill = document.querySelector('.power-fill');
    let width = 0;
    
    const animate = () => {
        width += 2;
        if (width <= 100) {
            powerFill.style.width = width + '%';
            setTimeout(animate, 50);
        }
    };
    
    animate();
}

// Agregar efectos de hover
function addHoverEffects() {
    const buttons = document.querySelectorAll('button, .action-btn');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Agregar estilos CSS dinámicos para animaciones
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes reactorStartup {
        0% {
            transform: scale(0.5);
            opacity: 0;
        }
        50% {
            transform: scale(1.2);
            opacity: 0.8;
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .result-item {
        background: rgba(0, 17, 34, 0.8);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #00d4ff;
    }
    
    .result-header h4 {
        color: #00d4ff;
        margin: 0;
    }
    
    .result-time {
        color: #b0b0b0;
        font-size: 0.8rem;
    }
    
    .result-content pre {
        background: rgba(0, 0, 0, 0.5);
        border: 1px solid #00d4ff;
        border-radius: 5px;
        padding: 15px;
        color: #00d4ff;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
    }
    
    .module-placeholder {
        text-align: center;
        padding: 40px;
        color: #00d4ff;
    }
    
    .module-placeholder h4 {
        margin-bottom: 20px;
        text-shadow: 0 0 10px #00d4ff;
    }
    
    .recording {
        animation: recordingPulse 1s infinite;
    }
    
    @keyframes recordingPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
`;
document.head.appendChild(style);

console.log('🎯 Tony Stark Interface JavaScript loaded successfully'); 