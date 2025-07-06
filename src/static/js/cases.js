/**
 * JavaScript para Casos de Ciberinteligencia
 * Maneja la interfaz RAG y análisis de casos
 */

// Variables globales
let currentCaseId = null;
let systemStatus = {
    rag_available: false,
    openai_connected: false,
    vector_db_ready: false
};

// Inicialización cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Cyber Intelligence Cases Interface Loading...');
    
    initializeCasesInterface();
    setupEventListeners();
    checkSystemStatus();
});

// Inicializar interfaz de casos
function initializeCasesInterface() {
    // Ocultar sección de caso actual inicialmente
    const currentCaseSection = document.getElementById('currentCaseSection');
    if (currentCaseSection) {
        currentCaseSection.style.display = 'none';
    }
    
    // Configurar estado inicial
    updateSystemStatusDisplay('INITIALIZING...');
    console.log('✅ Cases interface initialized');
}

// Configurar event listeners
function setupEventListeners() {
    // Formulario de creación de caso
    const createCaseForm = document.getElementById('createCaseForm');
    if (createCaseForm) {
        createCaseForm.addEventListener('submit', handleCreateCase);
    }
    
    // Botón de toggle del panel de creación
    const toggleCreatePanel = document.getElementById('toggleCreatePanel');
    if (toggleCreatePanel) {
        toggleCreatePanel.addEventListener('click', toggleCreatePanel);
    }
    
    // Botón de procesar texto
    const processTextBtn = document.getElementById('processTextBtn');
    if (processTextBtn) {
        processTextBtn.addEventListener('click', handleProcessText);
    }
    
    // Botón de ejecutar consulta
    const executeQueryBtn = document.getElementById('executeQueryBtn');
    if (executeQueryBtn) {
        executeQueryBtn.addEventListener('click', handleExecuteQuery);
    }
    
    // Botón de limpiar texto
    const clearTextBtn = document.getElementById('clearTextBtn');
    if (clearTextBtn) {
        clearTextBtn.addEventListener('click', clearTextInput);
    }
    
    // Botón de limpiar resultados
    const clearResultsBtn = document.getElementById('clearResultsBtn');
    if (clearResultsBtn) {
        clearResultsBtn.addEventListener('click', clearResults);
    }
    
    // Botón de resumen de caso
    const caseSummaryBtn = document.getElementById('caseSummaryBtn');
    if (caseSummaryBtn) {
        caseSummaryBtn.addEventListener('click', showCaseSummary);
    }
    
    // Botón de nuevo caso
    const newCaseBtn = document.getElementById('newCaseBtn');
    if (newCaseBtn) {
        newCaseBtn.addEventListener('click', startNewCase);
    }
    
    // Botón de exportar resultados
    const exportResultsBtn = document.getElementById('exportResultsBtn');
    if (exportResultsBtn) {
        exportResultsBtn.addEventListener('click', exportResults);
    }
    
    // Modal de resumen
    const closeSummaryModal = document.getElementById('closeSummaryModal');
    if (closeSummaryModal) {
        closeSummaryModal.addEventListener('click', closeSummaryModalFunc);
    }
    
    // Cerrar modal al hacer clic fuera
    const summaryModal = document.getElementById('summaryModal');
    if (summaryModal) {
        summaryModal.addEventListener('click', function(e) {
            if (e.target === summaryModal) {
                closeSummaryModalFunc();
            }
        });
    }
    
    console.log('✅ Event listeners configured');
}

// Verificar estado del sistema
async function checkSystemStatus() {
    try {
        showLoading('Checking system status...');
        
        const response = await fetch('/api/status');
        const data = await response.json();
        
        systemStatus.rag_available = data.rag_available || false;
        
        if (data.rag_system) {
            systemStatus.openai_connected = data.rag_system.openai_status?.success || false;
            systemStatus.vector_db_ready = data.rag_system.rag_system?.vector_store?.total_documents !== undefined;
        }
        
        updateSystemStatusDisplay();
        updateSystemInfoCards(data);
        
        console.log('📊 System status:', systemStatus);
        
    } catch (error) {
        console.error('❌ Error checking system status:', error);
        updateSystemStatusDisplay('SYSTEM ERROR');
        showNotification('Error checking system status', 'error');
    } finally {
        hideLoading();
    }
}

// Actualizar display del estado del sistema
function updateSystemStatusDisplay(customText = null) {
    const statusText = document.getElementById('systemStatusText');
    const statusLight = document.getElementById('systemStatus');
    
    if (!statusText || !statusLight) return;
    
    if (customText) {
        statusText.textContent = customText;
        return;
    }
    
    if (systemStatus.rag_available && systemStatus.openai_connected) {
        statusText.textContent = 'RAG SYSTEM ONLINE';
        statusLight.classList.add('active');
    } else if (systemStatus.rag_available) {
        statusText.textContent = 'RAG AVAILABLE - LLM OFFLINE';
        statusLight.classList.remove('active');
    } else {
        statusText.textContent = 'BASIC MODE - RAG UNAVAILABLE';
        statusLight.classList.remove('active');
    }
}

// Actualizar tarjetas de información del sistema
function updateSystemInfoCards(data) {
    // Vector Database
    const vectorDbStatus = document.getElementById('vectorDbStatus');
    if (vectorDbStatus) {
        if (data.rag_system?.rag_system?.vector_store) {
            const vectorInfo = data.rag_system.rag_system.vector_store;
            vectorDbStatus.textContent = `${vectorInfo.total_documents || 0} docs`;
        } else {
            vectorDbStatus.textContent = 'Offline';
        }
    }
    
    // AI Model
    const aiModelStatus = document.getElementById('aiModelStatus');
    if (aiModelStatus) {
        if (data.rag_system?.openai_status?.success) {
            aiModelStatus.textContent = data.rag_system.openai_status.model || 'Connected';
        } else {
            aiModelStatus.textContent = 'Disconnected';
        }
    }
    
    // NLP Engine
    const nlpStatus = document.getElementById('nlpStatus');
    if (nlpStatus) {
        if (data.rag_system?.rag_system?.nlp_processor) {
            nlpStatus.textContent = 'Active';
        } else {
            nlpStatus.textContent = 'Inactive';
        }
    }
    
    // Active Cases
    const activeCases = document.getElementById('activeCases');
    if (activeCases) {
        activeCases.textContent = data.rag_system?.case_manager?.active_cases || '0';
    }
}

// Manejar creación de caso
async function handleCreateCase(event) {
    event.preventDefault();
    
    if (!systemStatus.rag_available) {
        showNotification('RAG system not available', 'error');
        return;
    }
    
    const formData = new FormData(event.target);
    const caseData = {
        title: formData.get('title'),
        case_type: formData.get('case_type'),
        description: formData.get('description')
    };
    
    try {
        showLoading('Creating case...');
        
        const response = await fetch('/api/cases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(caseData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentCaseId = result.case_id;
            showCurrentCase(caseData, result.case_id);
            showNotification(`Case created: ${result.case_id}`, 'success');
            
            // Limpiar formulario
            event.target.reset();
        } else {
            showNotification(result.error || 'Error creating case', 'error');
        }
        
    } catch (error) {
        console.error('Error creating case:', error);
        showNotification('Error creating case', 'error');
    } finally {
        hideLoading();
    }
}

// Mostrar caso actual
function showCurrentCase(caseData, caseId) {
    const currentCaseSection = document.getElementById('currentCaseSection');
    const createPanel = document.querySelector('.case-creation-panel');
    
    if (currentCaseSection) {
        currentCaseSection.style.display = 'block';
        
        // Actualizar información del caso
        document.getElementById('currentCaseTitle').textContent = `Case: ${caseData.title}`;
        document.getElementById('currentCaseId').textContent = `ID: ${caseId}`;
        document.getElementById('currentCaseType').textContent = `Type: ${caseData.case_type}`;
        document.getElementById('currentCaseStatus').textContent = 'Status: Active';
    }
    
    // Colapsar panel de creación
    if (createPanel) {
        const content = createPanel.querySelector('.panel-content');
        const toggleBtn = createPanel.querySelector('.collapse-btn i');
        if (content && toggleBtn) {
            content.style.display = 'none';
            toggleBtn.className = 'fas fa-chevron-down';
        }
    }
}

// Manejar procesamiento de texto
async function handleProcessText() {
    if (!currentCaseId) {
        showNotification('Please create a case first', 'warning');
        return;
    }
    
    if (!systemStatus.rag_available) {
        showNotification('RAG system not available', 'error');
        return;
    }
    
    const textInput = document.getElementById('textInput');
    const text = textInput.value.trim();
    
    if (!text) {
        showNotification('Please enter some text to process', 'warning');
        return;
    }
    
    try {
        showLoading('Processing text with AI...');
        
        const response = await fetch(`/api/cases/${currentCaseId}/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayProcessingResults(result);
            showNotification('Text processed successfully', 'success');
        } else {
            showNotification(result.error || 'Error processing text', 'error');
        }
        
    } catch (error) {
        console.error('Error processing text:', error);
        showNotification('Error processing text', 'error');
    } finally {
        hideLoading();
    }
}

// Manejar ejecución de consulta
async function handleExecuteQuery() {
    if (!currentCaseId) {
        showNotification('Please create a case first', 'warning');
        return;
    }
    
    if (!systemStatus.rag_available) {
        showNotification('RAG system not available', 'error');
        return;
    }
    
    const queryInput = document.getElementById('queryInput');
    const queryType = document.getElementById('queryType');
    
    const query = queryInput.value.trim();
    const type = queryType.value;
    
    if (!query) {
        showNotification('Please enter a query', 'warning');
        return;
    }
    
    try {
        showLoading('Executing query...');
        
        const response = await fetch(`/api/cases/${currentCaseId}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                query_type: type
            })
        });
        
        const result = await response.json();
        
        if (result.llm_response) {
            displayQueryResults(result);
            showNotification('Query executed successfully', 'success');
            queryInput.value = ''; // Limpiar input
        } else {
            showNotification(result.error || 'Error executing query', 'error');
        }
        
    } catch (error) {
        console.error('Error executing query:', error);
        showNotification('Error executing query', 'error');
    } finally {
        hideLoading();
    }
}

// Mostrar resultados de procesamiento
function displayProcessingResults(result) {
    const resultsContent = document.getElementById('resultsContent');
    
    const resultsHtml = `
        <div class="processing-results">
            <div class="result-header">
                <h4><i class="fas fa-cogs"></i> TEXT PROCESSING RESULTS</h4>
                <span class="result-timestamp">${new Date().toLocaleTimeString()}</span>
            </div>
            
            <div class="result-section">
                <h5><i class="fas fa-brain"></i> AI Analysis</h5>
                <div class="ai-response">
                    ${result.rag_analysis?.llm_response || 'No AI response available'}
                </div>
            </div>
            
            ${result.processed_text?.entities ? `
            <div class="result-section">
                <h5><i class="fas fa-tags"></i> Extracted Entities (${result.processed_text.entities.length})</h5>
                <div class="entities-list">
                    ${result.processed_text.entities.slice(0, 10).map(entity => 
                        `<span class="entity-tag">${entity.text} (${entity.label})</span>`
                    ).join('')}
                </div>
            </div>` : ''}
            
            ${result.processed_text?.keywords ? `
            <div class="result-section">
                <h5><i class="fas fa-key"></i> Keywords</h5>
                <div class="keywords-list">
                    ${result.processed_text.keywords.slice(0, 15).map(keyword => 
                        `<span class="keyword-tag">${keyword}</span>`
                    ).join('')}
                </div>
            </div>` : ''}
            
            ${result.processed_text?.iocs && Object.keys(result.processed_text.iocs).length > 0 ? `
            <div class="result-section">
                <h5><i class="fas fa-shield-alt"></i> Indicators of Compromise (IoCs)</h5>
                <div class="iocs-list">
                    ${Object.entries(result.processed_text.iocs).map(([type, items]) => 
                        `<div class="ioc-group">
                            <strong>${type.replace('_', ' ').toUpperCase()}:</strong>
                            ${items.map(item => `<span class="ioc-item">${item}</span>`).join('')}
                        </div>`
                    ).join('')}
                </div>
            </div>` : ''}
            
            <div class="result-stats">
                <span>Processing Time: ${result.processing_time?.toFixed(2)}s</span>
                <span>Document ID: ${result.document_id}</span>
                <span>Similar Cases: ${result.rag_analysis?.similar_cases?.length || 0}</span>
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = resultsHtml;
}

// Mostrar resultados de consulta
function displayQueryResults(result) {
    const resultsContent = document.getElementById('resultsContent');
    
    const resultsHtml = `
        <div class="query-results">
            <div class="result-header">
                <h4><i class="fas fa-search"></i> QUERY RESULTS</h4>
                <span class="result-timestamp">${new Date().toLocaleTimeString()}</span>
            </div>
            
            <div class="query-info">
                <strong>Query:</strong> ${result.query}
                <span class="query-stats">
                    ${result.retrieved_documents} docs retrieved | 
                    ${result.processing_time?.toFixed(2)}s processing time
                </span>
            </div>
            
            <div class="result-section">
                <h5><i class="fas fa-robot"></i> AI Response</h5>
                <div class="ai-response">
                    ${result.llm_response}
                </div>
            </div>
            
            ${result.ioc_analysis ? `
            <div class="result-section">
                <h5><i class="fas fa-shield-alt"></i> IoC Analysis</h5>
                <div class="ioc-analysis">
                    ${result.ioc_analysis}
                </div>
            </div>` : ''}
            
            ${result.extracted_iocs && Object.keys(result.extracted_iocs).length > 0 ? `
            <div class="result-section">
                <h5><i class="fas fa-exclamation-triangle"></i> Extracted IoCs</h5>
                <div class="iocs-list">
                    ${Object.entries(result.extracted_iocs).map(([type, items]) => 
                        `<div class="ioc-group">
                            <strong>${type.replace('_', ' ').toUpperCase()}:</strong>
                            ${items.map(item => `<span class="ioc-item">${item}</span>`).join('')}
                        </div>`
                    ).join('')}
                </div>
            </div>` : ''}
            
            ${result.similar_cases && result.similar_cases.length > 0 ? `
            <div class="result-section">
                <h5><i class="fas fa-link"></i> Similar Cases</h5>
                <div class="similar-cases">
                    ${result.similar_cases.map(similarCase => 
                        `<div class="similar-case">
                            <strong>Case ID:</strong> ${similarCase.case_id} 
                            <span class="similarity-score">(${(similarCase.avg_similarity * 100).toFixed(1)}% match)</span>
                        </div>`
                    ).join('')}
                </div>
            </div>` : ''}
        </div>
    `;
    
    resultsContent.innerHTML = resultsHtml;
}

// Funciones auxiliares
function clearTextInput() {
    const textInput = document.getElementById('textInput');
    if (textInput) {
        textInput.value = '';
    }
}

function clearResults() {
    const resultsContent = document.getElementById('resultsContent');
    if (resultsContent) {
        resultsContent.innerHTML = `
            <div class="no-results">
                <i class="fas fa-brain"></i>
                <p>No analysis performed yet. Process some text or make a query to see AI-powered results.</p>
            </div>
        `;
    }
}

function toggleCreatePanelFunc() {
    const content = document.getElementById('createPanelContent');
    const icon = document.querySelector('#toggleCreatePanel i');
    
    if (content && icon) {
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        } else {
            content.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    }
}

function startNewCase() {
    currentCaseId = null;
    const currentCaseSection = document.getElementById('currentCaseSection');
    if (currentCaseSection) {
        currentCaseSection.style.display = 'none';
    }
    
    clearResults();
    clearTextInput();
    
    // Mostrar panel de creación
    const createPanelContent = document.getElementById('createPanelContent');
    if (createPanelContent) {
        createPanelContent.style.display = 'block';
        const icon = document.querySelector('#toggleCreatePanel i');
        if (icon) {
            icon.className = 'fas fa-chevron-up';
        }
    }
}

function showLoading(text = 'PROCESSING...') {
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
    
    if (loadingText) {
        loadingText.textContent = text;
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Estilos dinámicos
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 17, 34, 0.95);
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
        max-width: 400px;
    `;
    
    document.body.appendChild(notification);
    
    // Remover después de 4 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

async function showCaseSummary() {
    if (!currentCaseId) {
        showNotification('No active case', 'warning');
        return;
    }
    
    try {
        showLoading('Loading case summary...');
        
        const response = await fetch(`/api/cases/${currentCaseId}/summary`);
        const summary = await response.json();
        
        const summaryModal = document.getElementById('summaryModal');
        const summaryModalBody = document.getElementById('summaryModalBody');
        
        if (summary.error) {
            summaryModalBody.innerHTML = `<p class="error">Error: ${summary.error}</p>`;
        } else {
            summaryModalBody.innerHTML = `
                <div class="case-summary">
                    <h4>Case Overview</h4>
                    <div class="summary-stats">
                        <div class="stat-item">
                            <label>Total Documents:</label>
                            <span>${summary.statistics?.total_documents || 0}</span>
                        </div>
                        <div class="stat-item">
                            <label>Document Types:</label>
                            <span>${Object.keys(summary.statistics?.document_types || {}).join(', ')}</span>
                        </div>
                        <div class="stat-item">
                            <label>Total Entities:</label>
                            <span>${summary.statistics?.total_entities || 0}</span>
                        </div>
                        <div class="stat-item">
                            <label>Total IoCs:</label>
                            <span>${summary.statistics?.total_iocs || 0}</span>
                        </div>
                    </div>
                    
                    ${summary.ai_summary ? `
                    <h4>AI-Generated Summary</h4>
                    <div class="ai-summary">
                        ${summary.ai_summary}
                    </div>` : ''}
                    
                    ${summary.statistics?.top_keywords ? `
                    <h4>Top Keywords</h4>
                    <div class="keywords-summary">
                        ${summary.statistics.top_keywords.map(([keyword, count]) => 
                            `<span class="keyword-tag">${keyword} (${count})</span>`
                        ).join('')}
                    </div>` : ''}
                </div>
            `;
        }
        
        summaryModal.style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading case summary:', error);
        showNotification('Error loading case summary', 'error');
    } finally {
        hideLoading();
    }
}

function closeSummaryModalFunc() {
    const summaryModal = document.getElementById('summaryModal');
    if (summaryModal) {
        summaryModal.style.display = 'none';
    }
}

function exportResults() {
    const resultsContent = document.getElementById('resultsContent');
    if (!resultsContent || !currentCaseId) {
        showNotification('No results to export', 'warning');
        return;
    }
    
    const content = resultsContent.textContent || resultsContent.innerText;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `case_${currentCaseId}_results_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    window.URL.revokeObjectURL(url);
    showNotification('Results exported successfully', 'success');
}

console.log('🎯 Cyber Intelligence Cases JavaScript loaded successfully');

// JavaScript para Casos de Ciberinteligencia
console.log('Cases JavaScript loaded'); 