// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/news-pipeline/visualize`;

// DOM Elements
const tickerSelect = document.getElementById('ticker-select');
const minRelevanceInput = document.getElementById('min-relevance');
const maxArticlesInput = document.getElementById('max-articles');
const processBtn = document.getElementById('process-btn');
const loadingIndicator = document.getElementById('loading-indicator');
const errorMessage = document.getElementById('error-message');
const pipelineContainer = document.getElementById('pipeline-container');
const finalResult = document.getElementById('final-result');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    processBtn.addEventListener('click', handleProcess);
    
    // Allow Enter key to trigger process (works with select too)
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && (document.activeElement === minRelevanceInput || document.activeElement === maxArticlesInput)) {
            handleProcess();
        }
    });
});

// Main processing function
async function handleProcess() {
    const symbol = tickerSelect.value.trim().toUpperCase();
    const minRelevance = parseFloat(minRelevanceInput.value);
    const maxArticles = parseInt(maxArticlesInput.value);

    // Validation
    if (!symbol) {
        showError('Please select a stock ticker symbol');
        return;
    }

    if (isNaN(minRelevance) || minRelevance < 0 || minRelevance > 1) {
        showError('Min relevance must be between 0 and 1');
        return;
    }

    if (isNaN(maxArticles) || maxArticles < 1) {
        showError('Max articles must be at least 1');
        return;
    }

    // Reset UI
    hideError();
    hidePipeline();
    hideFinalResult();
    showLoading();
    processBtn.disabled = true;

    try {
        // Call API
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                min_relevance: minRelevance,
                max_articles: maxArticles
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide loading
        hideLoading();

        // Display results
        if (data.status === 'error') {
            showError(data.error || 'An error occurred while processing the pipeline');
        } else {
            displayPipeline(data);
            displayFinalResult(data.final_result);
        }

    } catch (error) {
        hideLoading();
        showError(`Failed to connect to backend: ${error.message}. Make sure the backend is running on ${API_BASE_URL}`);
    } finally {
        processBtn.disabled = false;
    }
}

// Display pipeline steps
function displayPipeline(data) {
    pipelineContainer.innerHTML = '';
    pipelineContainer.classList.remove('hidden');

    const steps = data.steps || [];

    steps.forEach((step, index) => {
        const stepElement = createStepElement(step, index);
        pipelineContainer.appendChild(stepElement);

        // Add connector between steps (except after last step)
        if (index < steps.length - 1) {
            const connector = document.createElement('div');
            connector.className = 'step-connector';
            connector.textContent = '↓';
            pipelineContainer.appendChild(connector);
        }
    });

    // Add total duration
    const totalDuration = document.createElement('div');
    totalDuration.className = 'text-center mt-20';
    totalDuration.style.color = '#666';
    totalDuration.innerHTML = `<strong>Total Pipeline Duration: ${data.total_duration_ms}ms</strong>`;
    pipelineContainer.appendChild(totalDuration);
}

// Create step element
function createStepElement(step, index) {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'pipeline-step';

    const agentName = step.agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    const status = step.status || 'unknown';

    // Step header
    const header = document.createElement('div');
    header.className = 'step-header';

    const title = document.createElement('div');
    title.className = 'step-title';
    title.innerHTML = `<span>Step ${index + 1}: ${agentName}</span>`;

    const statusBadge = document.createElement('div');
    statusBadge.className = `step-status ${status}`;
    statusBadge.textContent = status === 'completed' ? '✓ Completed' : 
                              status === 'processing' ? '⏳ Processing' : 
                              status === 'error' ? '✗ Error' : 'Unknown';

    if (step.duration_ms) {
        statusBadge.textContent += ` (${step.duration_ms}ms)`;
    }

    header.appendChild(title);
    header.appendChild(statusBadge);

    // Step metrics
    const metrics = document.createElement('div');
    metrics.className = 'step-metrics';

    if (step.details) {
        const details = step.details;

        // Agent-specific metrics
        if (step.agent === 'news_fetch_agent') {
            addMetric(metrics, 'Raw Articles', details.raw_articles_count || details.final_articles_count || 0);
            addMetric(metrics, 'Final Articles', details.final_articles_count || details.final_articles?.length || 0);
            addMetric(metrics, 'Sources', details.sources_used?.length || 0);
            
            // Data source indicator
            const dataSource = details.data_source || 'unknown';
            const dataSourceLabel = dataSource === 'mock' ? '📦 Mock Data' : '🌐 Real API';
            addMetric(metrics, 'Data Source', dataSourceLabel);
            
            // API usage information
            if (details.api_usage && Array.isArray(details.api_usage) && details.api_usage.length > 0) {
                // Add separator
                const separator = document.createElement('div');
                separator.className = 'metric-item';
                separator.style.borderTop = '1px solid #e0e0e0';
                separator.style.marginTop = '8px';
                separator.style.paddingTop = '8px';
                metrics.appendChild(separator);
                
                details.api_usage.forEach(usage => {
                    if (usage.is_mock) {
                        addMetric(metrics, `${usage.source}`, '📦 Mock (Unlimited)', '#9e9e9e');
                    } else {
                        const remaining = usage.calls_remaining !== null && usage.calls_remaining !== undefined 
                            ? usage.calls_remaining 
                            : 'N/A';
                        // Color code: red if low (< 10), orange if medium (< 50), green otherwise
                        let remainingColor = '#4caf50'; // green
                        if (remaining !== 'N/A' && typeof remaining === 'number') {
                            if (remaining < 10) {
                                remainingColor = '#f44336'; // red
                            } else if (remaining < 50) {
                                remainingColor = '#ff9800'; // orange
                            }
                        }
                        addMetric(metrics, `${usage.source} Remaining`, remaining, remainingColor);
                        if (usage.rate_limit) {
                            addMetric(metrics, `${usage.source} Limit`, usage.rate_limit);
                        }
                    }
                });
            }
        } else if (step.agent === 'llm_sentiment_agent') {
            addMetric(metrics, 'Articles Processed', details.articles_processed || 0);
            addMetric(metrics, 'Cache Hits', details.cache_hits || 0);
            addMetric(metrics, 'Cache Misses', details.cache_misses || 0);
            if (details.cache_hit_rate !== undefined) {
                addMetric(metrics, 'Cache Hit Rate', `${(details.cache_hit_rate * 100).toFixed(1)}%`);
            }
        } else if (step.agent === 'sentiment_aggregator') {
            addMetric(metrics, 'News Count', details.news_count || 0);
            addMetric(metrics, 'Sentiment', details.aggregated_sentiment?.toFixed(3) || 'N/A');
            addMetric(metrics, 'Confidence', details.confidence?.toFixed(2) || 'N/A');
        }
    }

    // Step details (expandable)
    const detailsSection = document.createElement('div');
    detailsSection.className = 'step-details';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'details-toggle';
    toggleBtn.textContent = '▶ View Details';
    toggleBtn.addEventListener('click', () => {
        const content = detailsSection.querySelector('.details-content');
        if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            toggleBtn.textContent = '▶ View Details';
        } else {
            content.classList.add('expanded');
            toggleBtn.textContent = '▼ Hide Details';
        }
    });

    const detailsContent = document.createElement('div');
    detailsContent.className = 'details-content';
    detailsContent.innerHTML = `<div class="data-viewer">${formatJSON(step.details || {})}</div>`;

    detailsSection.appendChild(toggleBtn);
    detailsSection.appendChild(detailsContent);

    // Error message if any
    if (step.error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<strong>Error:</strong> ${step.error}`;
        
        // Show error trace if available (in details)
        if (step.details && step.details.error_trace) {
            const traceDiv = document.createElement('details');
            traceDiv.style.marginTop = '10px';
            const summary = document.createElement('summary');
            summary.textContent = 'Show Error Trace';
            summary.style.cursor = 'pointer';
            summary.style.color = '#c33';
            const traceContent = document.createElement('pre');
            traceContent.style.background = '#f8f8f8';
            traceContent.style.padding = '10px';
            traceContent.style.overflow = 'auto';
            traceContent.style.maxHeight = '200px';
            traceContent.textContent = step.details.error_trace;
            traceDiv.appendChild(summary);
            traceDiv.appendChild(traceContent);
            errorDiv.appendChild(traceDiv);
        }
        
        stepDiv.appendChild(errorDiv);
    }

    // Assemble step
    stepDiv.appendChild(header);
    stepDiv.appendChild(metrics);
    stepDiv.appendChild(detailsSection);

    return stepDiv;
}

// Add metric to metrics container
function addMetric(container, label, value, color = null) {
    const metric = document.createElement('div');
    metric.className = 'metric';
    
    const labelSpan = document.createElement('div');
    labelSpan.className = 'metric-label';
    labelSpan.textContent = label;
    
    const valueSpan = document.createElement('div');
    valueSpan.className = 'metric-value';
    valueSpan.textContent = value;
    if (color) {
        valueSpan.style.color = color;
    }
    
    metric.appendChild(labelSpan);
    metric.appendChild(valueSpan);
    container.appendChild(metric);
}

// Display final result
function displayFinalResult(result) {
    if (!result) {
        return;
    }

    finalResult.classList.remove('hidden');
    finalResult.innerHTML = '';

    const title = document.createElement('h2');
    title.textContent = '🎯 Final Result';
    finalResult.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'result-grid';

    // Symbol
    addResultItem(grid, 'Symbol', result.symbol || 'N/A');

    // Aggregated Sentiment
    const sentiment = result.aggregated_sentiment || 0;
    const sentimentLabel = result.sentiment_label || 'neutral';
    const sentimentBadge = `<span class="sentiment-badge ${sentimentLabel}">${sentimentLabel.toUpperCase()}</span>`;
    addResultItem(grid, 'Aggregated Sentiment', `${sentiment.toFixed(3)} ${sentimentBadge}`);

    // Confidence
    addResultItem(grid, 'Confidence', `${((result.confidence || 0) * 100).toFixed(1)}%`);

    // Impact
    const impact = result.impact || 'Low';
    const impactBadge = `<span class="impact-badge ${impact.toLowerCase()}">${impact}</span>`;
    addResultItem(grid, 'Impact', impactBadge);

    // News Count
    addResultItem(grid, 'News Count', result.news_count || 0);

    // Time Weighted
    addResultItem(grid, 'Time Weighted', result.time_weighted ? 'Yes' : 'No');

    finalResult.appendChild(grid);
}

// Add result item to grid
function addResultItem(container, label, value) {
    const item = document.createElement('div');
    item.className = 'result-item';
    
    const labelDiv = document.createElement('div');
    labelDiv.className = 'result-item-label';
    labelDiv.textContent = label;
    
    const valueDiv = document.createElement('div');
    valueDiv.className = 'result-item-value';
    valueDiv.innerHTML = value;
    
    item.appendChild(labelDiv);
    item.appendChild(valueDiv);
    container.appendChild(item);
}

// Format JSON for display
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// UI Helper Functions
function showLoading() {
    loadingIndicator.classList.remove('hidden');
}

function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function hidePipeline() {
    pipelineContainer.classList.add('hidden');
    pipelineContainer.innerHTML = '';
}

function hideFinalResult() {
    finalResult.classList.add('hidden');
    finalResult.innerHTML = '';
}

