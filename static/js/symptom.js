// Form elements
const form = document.getElementById('symptomForm');
const symptomsInput = document.getElementById('symptoms');
const durationInput = document.getElementById('duration');
const severityInput = document.getElementById('severity');
const symptomsError = document.getElementById('symptomsError');
const durationError = document.getElementById('durationError');
const severityError = document.getElementById('severityError');
const resultDiv = document.getElementById('symptomResult');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Validation functions
function validateSymptoms() {
    const value = symptomsInput.value.trim();
    if (value.length < 10) {
        symptomsError.textContent = 'Please provide more detailed symptoms (minimum 10 characters)';
        symptomsError.classList.remove('hidden');
        return false;
    }
    symptomsError.classList.add('hidden');
    return true;
}

function validateDuration() {
    const value = durationInput.value;
    if (!value) {
        durationError.textContent = 'Please select the duration of your symptoms';
        durationError.classList.remove('hidden');
        return false;
    }
    durationError.classList.add('hidden');
    return true;
}

function validateSeverity() {
    const value = severityInput.value;
    if (!value) {
        severityError.textContent = 'Please select the severity of your symptoms';
        severityError.classList.remove('hidden');
        return false;
    }
    severityError.classList.add('hidden');
    return true;
}

// Show/hide loading and error states
function showLoading() {
    loadingIndicator.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    errorMessage.classList.add('hidden');
}

function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove('hidden');
    resultDiv.classList.add('hidden');
}

// Handle form submission
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Validate all fields
    const isSymptomsValid = validateSymptoms();
    const isDurationValid = validateDuration();
    const isSeverityValid = validateSeverity();
    
    if (!isSymptomsValid || !isDurationValid || !isSeverityValid) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/check_symptoms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symptoms: symptomsInput.value.trim(),
                duration: durationInput.value,
                severity: severityInput.value
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze symptoms');
        }
        
        // Clear previous results
        document.getElementById('possibleConditions').innerHTML = '';
        document.getElementById('recommendations').innerHTML = '';
        
        // Add conditions
        if (data.conditions && data.conditions.length > 0) {
            const conditionsList = document.createElement('div');
            conditionsList.className = 'space-y-2';
            data.conditions.forEach(condition => {
                conditionsList.innerHTML += `
                    <div class="flex items-center space-x-2">
                        <i class="fas fa-circle text-primary text-xs"></i>
                        <span class="text-gray-700">${condition}</span>
                    </div>
                `;
            });
            document.getElementById('possibleConditions').appendChild(conditionsList);
        }
        
        // Add recommendations
        if (data.recommendations && data.recommendations.length > 0) {
            const recommendationsList = document.createElement('div');
            recommendationsList.className = 'space-y-2';
            data.recommendations.forEach(recommendation => {
                recommendationsList.innerHTML += `
                    <div class="flex items-center space-x-2">
                        <i class="fas fa-check-circle text-green-500 text-xs"></i>
                        <span class="text-gray-700">${recommendation}</span>
                    </div>
                `;
            });
            document.getElementById('recommendations').appendChild(recommendationsList);
        }
        
        hideLoading();
        resultDiv.classList.remove('hidden');
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        showError(error.message || 'An error occurred while checking symptoms. Please try again.');
    }
});

// Real-time validation
symptomsInput.addEventListener('input', validateSymptoms);
durationInput.addEventListener('change', validateDuration);
severityInput.addEventListener('change', validateSeverity); 