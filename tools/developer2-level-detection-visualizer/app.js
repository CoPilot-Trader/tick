// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/levels`;

// DOM Elements
const tickerSelect = document.getElementById('ticker-select');
const minStrengthInput = document.getElementById('min-strength');
const maxLevelsInput = document.getElementById('max-levels');
const timeframeSelect = document.getElementById('timeframe-select');
const projectFutureCheckbox = document.getElementById('project-future');
const projectionPeriodsInput = document.getElementById('projection-periods');
const projectionPeriodsGroup = document.getElementById('projection-periods-group');
const lookbackDaysInput = document.getElementById('lookback-days');
const detectBtn = document.getElementById('detect-btn');
const loadingIndicator = document.getElementById('loading-indicator');
const errorMessage = document.getElementById('error-message');
const priceOverview = document.getElementById('price-overview');
const levelsContainer = document.getElementById('levels-container');
const predictedLevelsSection = document.getElementById('predicted-levels-section');
const predictedLevelsDiv = document.getElementById('predicted-levels');
const metadataSection = document.getElementById('metadata-section');
const supportLevelsDiv = document.getElementById('support-levels');
const resistanceLevelsDiv = document.getElementById('resistance-levels');
const currentPriceValue = document.getElementById('current-price-value');
const currentPriceSymbol = document.getElementById('current-price-symbol');
const nearestSupport = document.getElementById('nearest-support');
const nearestResistance = document.getElementById('nearest-resistance');
const supportDistance = document.getElementById('support-distance');
const resistanceDistance = document.getElementById('resistance-distance');
const metadataGrid = document.getElementById('metadata-grid');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    detectBtn.addEventListener('click', handleDetect);
    
    // Show/hide projection periods input based on checkbox
    projectFutureCheckbox.addEventListener('change', (e) => {
        projectionPeriodsGroup.style.display = e.target.checked ? 'flex' : 'none';
    });
    
    // Allow Enter key to trigger detect
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && (
            document.activeElement === minStrengthInput || 
            document.activeElement === maxLevelsInput ||
            document.activeElement === projectionPeriodsInput ||
            document.activeElement === lookbackDaysInput
        )) {
            handleDetect();
        }
    });
});

// Main detection function
async function handleDetect() {
    const symbol = tickerSelect.value.trim().toUpperCase();
    const minStrength = parseInt(minStrengthInput.value);
    const maxLevels = parseInt(maxLevelsInput.value);
    const timeframe = timeframeSelect.value;
    const projectFuture = projectFutureCheckbox.checked;
    const projectionPeriods = parseInt(projectionPeriodsInput.value) || 20;
    const lookbackDaysValue = lookbackDaysInput.value.trim();
    const lookbackDays = lookbackDaysValue ? parseInt(lookbackDaysValue) : null;

    // Validation
    if (!symbol) {
        showError('Please select a stock ticker symbol');
        return;
    }

    if (isNaN(minStrength) || minStrength < 0 || minStrength > 100) {
        showError('Min strength must be between 0 and 100');
        return;
    }

    if (isNaN(maxLevels) || maxLevels < 1 || maxLevels > 20) {
        showError('Max levels must be between 1 and 20');
        return;
    }

    if (projectFuture && (isNaN(projectionPeriods) || projectionPeriods < 1 || projectionPeriods > 100)) {
        showError('Projection periods must be between 1 and 100');
        return;
    }

    if (lookbackDays !== null && (isNaN(lookbackDays) || lookbackDays < 1 || lookbackDays > 3650)) {
        showError('Lookback days must be between 1 and 3650');
        return;
    }

    // Reset UI
    hideError();
    hideResults();
    showLoading();
    detectBtn.disabled = true;

    try {
        // Build API URL with parameters
        const params = new URLSearchParams({
            min_strength: minStrength,
            max_levels: maxLevels,
            timeframe: timeframe
        });
        
        if (projectFuture) {
            params.append('project_future', 'true');
            params.append('projection_periods', projectionPeriods);
        }
        
        if (lookbackDays !== null) {
            params.append('lookback_days', lookbackDays);
        }
        
        const url = `${API_ENDPOINT}/${symbol}?${params.toString()}`;
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout (increased for large datasets)
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId); // Clear timeout if request completes

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail?.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide loading
        hideLoading();

        // Display results
        if (data.status === 'error') {
            showError(data.message || 'An error occurred while detecting levels');
        } else {
            displayResults(data);
        }

    } catch (error) {
        hideLoading();
        
        // Handle different error types
        let errorMessage = '';
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. The backend is taking too long to process. Try reducing the lookback period or using a different timeframe.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = `Failed to connect to backend: ${error.message}. Make sure the backend is running on ${API_BASE_URL}`;
        } else {
            errorMessage = `Error: ${error.message}. Please check your parameters and try again.`;
        }
        
        showError(errorMessage);
    } finally {
        detectBtn.disabled = false;
    }
}

// Display results
function displayResults(data) {
    // Display current price and nearest levels
    displayPriceOverview(data);
    
    // Display support levels
    displayLevels(data.support_levels || [], supportLevelsDiv, 'support');
    
    // Display resistance levels
    displayLevels(data.resistance_levels || [], resistanceLevelsDiv, 'resistance');
    
    // Display predicted future levels if available
    if (data.predicted_future_levels && data.predicted_future_levels.length > 0) {
        displayPredictedLevels(data.predicted_future_levels);
        predictedLevelsSection.classList.remove('hidden');
    } else {
        predictedLevelsSection.classList.add('hidden');
    }
    
    // Display metadata
    displayMetadata(data);
    
    // Show all sections
    priceOverview.classList.remove('hidden');
    levelsContainer.classList.remove('hidden');
    metadataSection.classList.remove('hidden');
}

// Display price overview
function displayPriceOverview(data) {
    const currentPrice = data.current_price || 0;
    const symbol = data.symbol || '';
    
    currentPriceValue.textContent = `$${currentPrice.toFixed(2)}`;
    currentPriceSymbol.textContent = symbol;
    
    // Find nearest support (highest support below current price)
    const supportLevels = data.support_levels || [];
    const nearestSupportLevel = supportLevels
        .filter(level => level.price < currentPrice)
        .sort((a, b) => b.price - a.price)[0];
    
    if (nearestSupportLevel) {
        const distance = ((currentPrice - nearestSupportLevel.price) / currentPrice * 100).toFixed(2);
        nearestSupport.textContent = `$${nearestSupportLevel.price.toFixed(2)}`;
        supportDistance.textContent = `${distance}% below`;
        supportDistance.className = 'nearest-distance';
    } else {
        nearestSupport.textContent = 'N/A';
        supportDistance.textContent = 'No support level found';
        supportDistance.className = 'nearest-distance';
    }
    
    // Find nearest resistance (lowest resistance above current price)
    const resistanceLevels = data.resistance_levels || [];
    const nearestResistanceLevel = resistanceLevels
        .filter(level => level.price > currentPrice)
        .sort((a, b) => a.price - b.price)[0];
    
    if (nearestResistanceLevel) {
        const distance = ((nearestResistanceLevel.price - currentPrice) / currentPrice * 100).toFixed(2);
        nearestResistance.textContent = `$${nearestResistanceLevel.price.toFixed(2)}`;
        resistanceDistance.textContent = `${distance}% above`;
        resistanceDistance.className = 'nearest-distance';
    } else {
        nearestResistance.textContent = 'N/A';
        resistanceDistance.textContent = 'No resistance level found';
        resistanceDistance.className = 'nearest-distance';
    }
}

// Display levels
function displayLevels(levels, container, type) {
    container.innerHTML = '';
    
    if (levels.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'empty-message';
        emptyMessage.textContent = `No ${type} levels detected with current filters`;
        container.appendChild(emptyMessage);
        return;
    }
    
    // Sort: Support (highest to lowest), Resistance (lowest to highest)
    const sortedLevels = type === 'support' 
        ? [...levels].sort((a, b) => b.price - a.price)
        : [...levels].sort((a, b) => a.price - b.price);
    
    sortedLevels.forEach(level => {
        const levelCard = createLevelCard(level, type);
        container.appendChild(levelCard);
    });
}

// Create level card
function createLevelCard(level, type) {
    const card = document.createElement('div');
    card.className = `level-card ${type}`;
    
    const price = level.price || 0;
    const strength = level.strength || 0;
    const touches = level.touches || 0;
    const validated = level.validated || false;
    const validationRate = level.validation_rate || 0;
    const breakoutProb = level.breakout_probability !== undefined ? level.breakout_probability : null;
    const hasVolumeConfirmation = level.has_volume_confirmation || false;
    const volumePercentile = level.volume_percentile !== undefined ? level.volume_percentile : null;
    const volume = level.volume !== undefined ? level.volume : null;
    
    // Strength color gradient
    const strengthColor = getStrengthColor(strength);
    
    // Breakout probability color (higher = more likely to break = more red)
    const breakoutColor = breakoutProb !== null ? getBreakoutColor(breakoutProb) : '#999';
    
    card.innerHTML = `
        <div class="level-header">
            <div class="level-price">$${price.toFixed(2)}</div>
            <div class="level-type-badge ${type}">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        </div>
        <div class="level-strength">
            <div class="strength-label">Strength: ${strength}/100</div>
            <div class="strength-bar-container">
                <div class="strength-bar" style="width: ${strength}%; background: ${strengthColor}"></div>
            </div>
        </div>
        ${breakoutProb !== null ? `
        <div class="level-breakout">
            <div class="breakout-label">Breakout Probability: ${breakoutProb.toFixed(1)}%</div>
            <div class="breakout-bar-container">
                <div class="breakout-bar" style="width: ${breakoutProb}%; background: ${breakoutColor}"></div>
            </div>
        </div>
        ` : ''}
        <div class="level-metrics">
            <div class="metric">
                <span class="metric-label">Touches:</span>
                <span class="metric-value">${touches}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Validated:</span>
                <span class="metric-value ${validated ? 'valid' : 'invalid'}">${validated ? '✓ Yes' : '✗ No'}</span>
            </div>
            ${validationRate > 0 ? `
            <div class="metric">
                <span class="metric-label">Validation Rate:</span>
                <span class="metric-value">${(validationRate * 100).toFixed(0)}%</span>
            </div>
            ` : ''}
        </div>
        ${hasVolumeConfirmation || volumePercentile !== null || volume !== null ? `
        <div class="level-volume">
            <div class="volume-header">
                <span class="volume-label">📊 Volume Information</span>
                ${hasVolumeConfirmation ? `<span class="volume-badge confirmed">✓ Confirmed</span>` : ''}
            </div>
            ${volumePercentile !== null ? `
            <div class="volume-metric">
                <span class="volume-metric-label">Volume Percentile:</span>
                <span class="volume-metric-value">${volumePercentile.toFixed(1)}%</span>
            </div>
            ` : ''}
            ${volume !== null ? `
            <div class="volume-metric">
                <span class="volume-metric-label">Volume:</span>
                <span class="volume-metric-value">${formatVolume(volume)}</span>
            </div>
            ` : ''}
        </div>
        ` : ''}
            ${level.projected_valid_until ? `
        <div class="level-projection">
            <div class="projection-header">⏱️ Level Projection</div>
            <div class="projection-metric">
                <span class="projection-label">Valid Until:</span>
                <span class="projection-value">${formatDate(level.projected_valid_until)}</span>
            </div>
            <div class="projection-metric">
                <span class="projection-label">Validity Probability:</span>
                <span class="projection-value">${level.projected_validity_probability?.toFixed(1) || 'N/A'}%</span>
            </div>
            <div class="projection-metric">
                <span class="projection-label">Projected Strength:</span>
                <span class="projection-value">${level.projected_strength?.toFixed(1) || 'N/A'}/100</span>
            </div>
        </div>
        ` : ''}
            ${level.first_touch || level.last_touch ? `
        <div class="level-dates">
            ${level.first_touch ? `<div class="date-item"><span class="date-label">First Touch:</span> <span class="date-value">${formatDate(level.first_touch)}</span></div>` : ''}
            ${level.last_touch ? `<div class="date-item"><span class="date-label">Last Touch:</span> <span class="date-value">${formatDate(level.last_touch)}</span></div>` : ''}
        </div>
        ` : ''}
    `;
    
    return card;
}

// Get strength color based on score
function getStrengthColor(strength) {
    if (strength >= 80) return '#4CAF50'; // Green - Very strong
    if (strength >= 60) return '#8BC34A'; // Light green - Strong
    if (strength >= 40) return '#FFC107'; // Amber - Moderate
    if (strength >= 20) return '#FF9800'; // Orange - Weak
    return '#F44336'; // Red - Very weak
}

// Get breakout probability color (higher = more red, lower = more green)
function getBreakoutColor(probability) {
    if (probability >= 70) return '#F44336'; // Red - High probability of breaking
    if (probability >= 50) return '#FF9800'; // Orange - Moderate probability
    if (probability >= 30) return '#FFC107'; // Amber - Low-moderate probability
    return '#4CAF50'; // Green - Low probability (strong level)
}

// Format volume number (e.g., 5000000 -> "5.0M")
function formatVolume(volume) {
    if (volume >= 1000000000) {
        return (volume / 1000000000).toFixed(1) + 'B';
    } else if (volume >= 1000000) {
        return (volume / 1000000).toFixed(1) + 'M';
    } else if (volume >= 1000) {
        return (volume / 1000).toFixed(1) + 'K';
    }
    return volume.toString();
}

// Display predicted future levels
function displayPredictedLevels(predictedLevels) {
    predictedLevelsDiv.innerHTML = '';
    
    if (predictedLevels.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'empty-message';
        emptyMessage.textContent = 'No future levels predicted';
        predictedLevelsDiv.appendChild(emptyMessage);
        return;
    }
    
    // Group by type
    const supportLevels = predictedLevels.filter(l => l.type === 'support');
    const resistanceLevels = predictedLevels.filter(l => l.type === 'resistance');
    
    // Display support predictions
    if (supportLevels.length > 0) {
        const section = document.createElement('div');
        section.className = 'predicted-section';
        section.innerHTML = '<h4 style="color: #4CAF50; margin-bottom: 10px;">Predicted Support Levels</h4>';
        const list = document.createElement('div');
        list.className = 'levels-list';
        supportLevels.forEach(level => {
            list.appendChild(createPredictedLevelCard(level));
        });
        section.appendChild(list);
        predictedLevelsDiv.appendChild(section);
    }
    
    // Display resistance predictions
    if (resistanceLevels.length > 0) {
        const section = document.createElement('div');
        section.className = 'predicted-section';
        section.innerHTML = '<h4 style="color: #f44336; margin-bottom: 10px;">Predicted Resistance Levels</h4>';
        const list = document.createElement('div');
        list.className = 'levels-list';
        resistanceLevels.forEach(level => {
            list.appendChild(createPredictedLevelCard(level));
        });
        section.appendChild(list);
        predictedLevelsDiv.appendChild(section);
    }
}

// Create predicted level card
function createPredictedLevelCard(level) {
    const card = document.createElement('div');
    card.className = `level-card ${level.type} predicted`;
    
    const price = level.price || 0;
    const confidence = level.confidence || 0;
    const source = level.source || 'pattern';
    
    card.innerHTML = `
        <div class="level-header">
            <div class="level-price">$${price.toFixed(2)}</div>
            <div class="level-type-badge ${level.type}">${level.type.charAt(0).toUpperCase() + level.type.slice(1)}</div>
        </div>
        <div class="predicted-badge">🔮 PREDICTED</div>
        <div class="level-metrics">
            <div class="metric">
                <span class="metric-label">Confidence:</span>
                <span class="metric-value">${confidence.toFixed(1)}%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Source:</span>
                <span class="metric-value">${source.replace('_', ' ')}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Timeframe:</span>
                <span class="metric-value">${level.projected_timeframe || 'N/A'} periods</span>
            </div>
        </div>
    `;
    
    return card;
}

// Get lookback days display
function getLookbackDaysDisplay(metadata) {
    if (!metadata) return 'N/A';
    
    const lookbackDays = metadata.lookback_days;
    const isCustom = metadata.custom_lookback || metadata.lookback_days_source === 'custom';
    const defaultDays = metadata.default_lookback_days;
    const timeframe = metadata.timeframe || '1d';
    
    if (isCustom && lookbackDays) {
        // User selected custom lookback days
        return `${lookbackDays} days (Custom)`;
    } else if (lookbackDays && defaultDays) {
        // Using default lookback days based on timeframe
        return `${lookbackDays} days (Default for ${timeframe})`;
    } else if (lookbackDays) {
        // Just show the days if available
        return `${lookbackDays} days`;
    } else if (defaultDays) {
        // Show default if available
        return `${defaultDays} days (Default)`;
    }
    
    return 'N/A';
}

// Get data source display with icon
function getDataSourceDisplay(source, label) {
    if (!source && !label) return 'N/A';
    
    const displayLabel = label || source || 'Unknown';
    let icon = '';
    let className = 'data-source';
    
    if (source === 'yfinance' || displayLabel.includes('Yahoo Finance')) {
        icon = '🌐';
        className += ' data-source-real';
    } else if (source === 'data_agent' || displayLabel.includes('Data Agent')) {
        icon = '🔗';
        className += ' data-source-real';
    } else if (source === 'mock_data' || displayLabel.includes('Mock')) {
        icon = '📊';
        className += ' data-source-mock';
    }
    
    return `<span class="${className}">${icon} ${displayLabel}</span>`;
}

// Display metadata
function displayMetadata(data) {
    metadataGrid.innerHTML = '';
    
    const metadata = data.metadata || {};
    const apiMetadata = data.api_metadata || {};
    
    const metadataItems = [
        { label: 'Total Levels', value: data.total_levels || 0 },
        { label: 'Support Levels', value: (data.support_levels || []).length },
        { label: 'Resistance Levels', value: (data.resistance_levels || []).length },
        { label: 'Timeframe', value: data.timeframe || metadata.timeframe || '1d' },
        { label: 'Lookback Days', value: getLookbackDaysDisplay(metadata) },
        { label: 'Data Source', value: getDataSourceDisplay(metadata.data_source, metadata.data_source_label) },
        { label: 'Peaks Detected', value: metadata.peaks_detected || 'N/A' },
        { label: 'Valleys Detected', value: metadata.valleys_detected || 'N/A' },
        { label: 'Data Points', value: metadata.data_points || 'N/A' },
        { label: 'Processing Time', value: data.processing_time_seconds ? `${data.processing_time_seconds}s` : 'N/A' },
        { label: 'API Response Time', value: apiMetadata.processing_time_seconds ? `${apiMetadata.processing_time_seconds}s` : 'N/A' }
    ];
    
    if (data.predicted_future_levels && data.predicted_future_levels.length > 0) {
        metadataItems.push({ 
            label: 'Predicted Levels', 
            value: data.predicted_future_levels.length 
        });
        metadataItems.push({ 
            label: 'Projection Periods', 
            value: data.projection_periods || 'N/A' 
        });
    }
    
    metadataItems.forEach(item => {
        const metadataItem = document.createElement('div');
        metadataItem.className = 'metadata-item';
        metadataItem.innerHTML = `
            <div class="metadata-label">${item.label}</div>
            <div class="metadata-value">${item.value}</div>
        `;
        metadataGrid.appendChild(metadataItem);
    });
}

// Format date
function formatDate(dateString) {
    // Handle null, undefined, or empty strings
    if (!dateString || dateString === 'null' || dateString === 'undefined' || dateString === '') {
        return 'N/A';
    }
    
    try {
        const date = new Date(dateString);
        
        // Check if date is valid (Invalid Date will have NaN as time value)
        if (isNaN(date.getTime())) {
            return 'N/A';
        }
        
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        // If any error occurs, return N/A
        return 'N/A';
    }
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

function hideResults() {
    priceOverview.classList.add('hidden');
    levelsContainer.classList.add('hidden');
    predictedLevelsSection.classList.add('hidden');
    metadataSection.classList.add('hidden');
    supportLevelsDiv.innerHTML = '';
    resistanceLevelsDiv.innerHTML = '';
    predictedLevelsDiv.innerHTML = '';
    metadataGrid.innerHTML = '';
}
