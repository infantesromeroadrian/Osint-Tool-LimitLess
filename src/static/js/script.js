// Variables globales para el sistema Tony Stark
let startTime = Date.now();
let queryCount = 0;
let systemOnline = true;

// Inicialización del sistema cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    startSystemMonitoring();
    
    // Agregar prueba del sistema RAG
    setTimeout(testRAGSystem, 2000);
    
    // Verificación automática del sistema
    setTimeout(() => {
        if (typeof verifySystem === 'function') {
            verifySystem();
        }
    }, 3000);
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

// FUNCIÓN COMENTADA - Se usa la del HTML
/* 
async function executeCommand_OLD() {
    console.log('🔍 EXECUTE COMMAND CALLED!');
    
    const commandInput = document.getElementById('commandInput');
    const command = commandInput.value.trim();
    
    console.log('🔍 Command input found:', !!commandInput);
    console.log('🔍 Command value:', command);
    
    if (!command) {
        console.log('🔍 No command provided');
        showNotification('Please enter a command', 'warning');
        return;
    }
    
    if (!systemOnline) {
        console.log('🔍 System offline');
        showNotification('System offline - Cannot execute command', 'error');
        return;
    }
    
    console.log('🔍 Starting command execution...');
    
    // Mostrar loading
    showLoading(true);
    
    // Agregar al log
    addLogEntry(`Executing: ${command}`);
    
    // Incrementar contador
    queryCount++;
    document.getElementById('queryCount').textContent = queryCount;
    
    try {
        console.log('🔍 SENDING REQUEST...');
        console.log('🔍 Command:', command);
        
        // Enviar comando al sistema RAG conversacional
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: command })
        });
        
        console.log('🔍 RESPONSE RECEIVED');
        console.log('🔍 Status:', response.status);
        console.log('🔍 OK:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('🔍 DATA PARSED');
        console.log('🔍 Data:', data);
        
        // Verificar si hay error en los datos
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Mostrar resultados
        // displayConversationalResults(command, data); // DESHABILITADO TEMPORALMENTE
        
        // USAR MÉTODO ULTRA-SIMPLE TEMPORALMENTE
        console.log('🔍 Using ultra-simple display method...');
        const answer = data.answer || data.response || 'No answer found';
        
        // Mostrar en alert
        alert(`✅ RESPUESTA DEL SISTEMA RAG:\n\n${answer}\n\nSesión: ${data.session_id}\nMemoria: ${data.conversation_length} mensajes`);
        
        // También agregar al chat container
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            const successDiv = document.createElement('div');
            successDiv.style.cssText = 'background: rgba(0, 255, 0, 0.2); border: 1px solid green; color: white; padding: 15px; margin: 10px; border-radius: 8px; font-family: monospace;';
            successDiv.innerHTML = `
                <strong>✅ RAG RESPONSE RECEIVED:</strong><br>
                <strong>Query:</strong> ${command}<br>
                <strong>Answer:</strong> ${answer}<br>
                <strong>Session:</strong> ${data.session_id}<br>
                <strong>Memory:</strong> ${data.conversation_length} messages<br>
                <strong>Processing Time:</strong> ${data.processing_time}s<br>
                <strong>Timestamp:</strong> ${new Date().toLocaleString()}
            `;
            chatContainer.appendChild(successDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Limpiar input
        commandInput.value = '';
        
        // Agregar al log
        addLogEntry(`RAG query executed successfully`);
        
    } catch (error) {
        console.error('❌ Error executing command:', error);
        
        // Mostrar error en la interfaz
        const resultsContent = document.getElementById('resultsContent');
        resultsContent.innerHTML = `
            <div style="border: 1px solid #ff4444; padding: 15px; margin: 10px 0; background: rgba(34, 0, 17, 0.9);">
                <h4 style="color: #ff4444;">❌ ERROR</h4>
                <div style="color: white; margin: 10px 0;">
                    ${error.message}
                </div>
            </div>
        `;
        
        showNotification('Error executing command', 'error');
        addLogEntry(`Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}
*/

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

// Mostrar resultados conversacionales del sistema RAG (VERSIÓN SIMPLE)
function displayConversationalResults(command, data) {
    console.log('🎨 displayConversationalResults called with:', { command, data });
    
    const resultsContent = document.getElementById('resultsContent');
    
    // Validar que data existe
    if (!data) {
        console.error('❌ No data provided to displayConversationalResults');
        if (resultsContent) {
            resultsContent.innerHTML = `<div class="error">❌ No data received</div>`;
        }
        return;
    }
    
    // CRÍTICO: Verificar que el elemento existe
    if (!resultsContent) {
        console.error('❌ CRITICAL ERROR: resultsContent element not found!');
        console.error('❌ Running system verification...');
        
        // Ejecutar verificación del sistema
        if (typeof verifySystem === 'function') {
            verifySystem();
        }
        
        // Mostrar error en el chat en su lugar
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            const errorMessage = `
                <div style="color: red; padding: 15px; margin: 10px; border: 1px solid red;">
                    ❌ CRITICAL ERROR: Display element missing.<br>
                    Check console for system verification results.
                </div>
            `;
            chatContainer.innerHTML += errorMessage;
        }
        return;
    }
    
    // Obtener respuesta - probar múltiples campos
    let answer = 'No response found';
    if (data.answer) {
        answer = data.answer;
    } else if (data.response) {
        answer = data.response;
    } else if (data.result) {
        answer = data.result;
    }
    
    console.log('🎨 Final answer:', answer);
    console.log('🎨 Answer type:', typeof answer);
    
    // Crear HTML SIMPLE
    const simpleHtml = `
        <div style="border: 1px solid #00d4ff; padding: 15px; margin: 10px 0; background: rgba(0, 17, 34, 0.9);">
            <h4 style="color: #00d4ff;">🔍 QUERY: ${command}</h4>
            <div style="margin: 10px 0; padding: 10px; background: rgba(0, 212, 255, 0.1); border-left: 4px solid #00d4ff;">
                <strong style="color: #00d4ff;">🤖 Response:</strong><br>
                <span style="color: white;">${answer}</span>
            </div>
            <div style="color: #888; font-size: 0.9em;">
                Session: ${data.session_id || 'default'} | 
                Memory: ${data.conversation_length || 0} msgs | 
                Time: ${data.processing_time ? data.processing_time.toFixed(2) + 's' : 'N/A'}
            </div>
        </div>
    `;
    
    console.log('🎨 Generated simple HTML (first 200 chars):', simpleHtml.substring(0, 200));
    resultsContent.innerHTML = simpleHtml;
    
    console.log('✅ Results displayed successfully');
}

// Limpiar resultados
function clearResults() {
    const resultsContent = document.getElementById('resultsContent');
    if (resultsContent) {
        resultsContent.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>No analysis performed yet. Execute a query to see results.</p>
            </div>
        `;
        console.log('✅ Results cleared');
    } else {
        console.error('❌ resultsContent element not found');
    }
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

// Función de prueba para diagnosticar el problema
function testRAGSystem() {
    console.log('🧪 Testing RAG System...');
    simpleTest(); // Usar la función simple
}

// Función de prueba ULTRA simple para diagnosticar
function simpleTest() {
    console.log('🔥 SIMPLE TEST STARTING...');
    
    const testData = {
        query: "Test simple"
    };
    
    console.log('🔥 Sending:', JSON.stringify(testData));
    
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData)
    })
    .then(response => {
        console.log('🔥 Response received:', response);
        console.log('🔥 Response status:', response.status);
        console.log('🔥 Response ok:', response.ok);
        
        return response.text(); // Usar text() en lugar de json() para ver raw
    })
    .then(rawText => {
        console.log('🔥 Raw response text:', rawText);
        
        try {
            const data = JSON.parse(rawText);
            console.log('🔥 Parsed JSON:', data);
            console.log('🔥 Answer field:', data.answer);
            console.log('🔥 Answer type:', typeof data.answer);
            
            if (data.answer) {
                alert('✅ SUCCESS: ' + data.answer);
            } else {
                alert('❌ PROBLEM: No answer field found');
            }
        } catch (e) {
            console.error('🔥 JSON parse error:', e);
            alert('❌ PROBLEM: Invalid JSON response');
        }
    })
    .catch(error => {
        console.error('🔥 Fetch error:', error);
        alert('❌ PROBLEM: Network error');
    });
}

// Agregar botón de prueba simple
document.addEventListener('DOMContentLoaded', function() {
    // Crear botón de prueba en la interfaz
    const testButton = document.createElement('button');
    testButton.textContent = '🔥 SIMPLE TEST';
    testButton.style.position = 'fixed';
    testButton.style.top = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px';
    testButton.style.backgroundColor = '#ff4444';
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.cursor = 'pointer';
    testButton.onclick = simpleTest;
    
    document.body.appendChild(testButton);
});

// Test ULTRA SIMPLE que muestra resultado en alert
function ultraSimpleTest() {
    console.log('🚀 ULTRA SIMPLE TEST STARTING...');
    
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'Test simple' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('🚀 Raw data received:', data);
        
        const answer = data.answer || data.response || 'No answer found';
        console.log('🚀 Answer extracted:', answer);
        
        // Mostrar en alert para ver si funciona
        alert(`RESPUESTA RECIBIDA:\n\n${answer}`);
        
        // También mostrar en el chat container existente
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.innerHTML += `
                <div style="background: green; color: white; padding: 15px; margin: 10px; border-radius: 8px;">
                    <strong>✅ ÉXITO:</strong><br>
                    ${answer}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('🚀 Error:', error);
        alert(`ERROR: ${error.message}`);
    });
}

// Hacer función accesible globalmente
window.ultraSimpleTest = ultraSimpleTest;

// Función de verificación completa del sistema
function verifySystem() {
    console.log('🔧 SYSTEM VERIFICATION STARTING...');
    
    // Verificar elemento resultsContent
    const resultsContent = document.getElementById('resultsContent');
    console.log('🔧 resultsContent element:', resultsContent);
    console.log('🔧 resultsContent exists:', !!resultsContent);
    
    if (!resultsContent) {
        console.error('❌ CRITICAL: resultsContent element missing!');
        return false;
    }
    
    // Verificar elemento commandInput
    const commandInput = document.getElementById('commandInput');
    console.log('🔧 commandInput exists:', !!commandInput);
    
    // Verificar función displayConversationalResults
    console.log('🔧 displayConversationalResults exists:', typeof displayConversationalResults);
    
    // Realizar prueba simple
    console.log('🔧 Testing resultsContent update...');
    resultsContent.innerHTML = `
        <div style="color: green; padding: 20px;">
            ✅ VERIFICATION SUCCESSFUL! 
            <br>Element found and working correctly.
            <br>Time: ${new Date().toLocaleTimeString()}
        </div>
    `;
    
    console.log('✅ SYSTEM VERIFICATION COMPLETE');
    return true;
}

console.log('🎯 Tony Stark Interface JavaScript loaded successfully'); 

// Función simple para test desde consola
window.testRAGFromConsole = function() {
    console.log('🧪 Testing RAG system from console...');
    
    // Usar la función sendChatMessage del HTML
    if (typeof sendChatMessage === 'function') {
        sendChatMessage('Test desde consola - dame los alias que hemos probado');
        console.log('✅ Test enviado usando sendChatMessage()');
    } else {
        console.error('❌ sendChatMessage function not found');
    }
}; 