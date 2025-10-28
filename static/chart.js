// ============================================
// EXPENSE TRACKER DASHBOARD - JAVASCRIPT
// ============================================

// ============================================
// MODAL FUNCTIONS
// ============================================

/**
 * Open Edit Modal with transaction data
 * @param {string} id - Transaction ID
 * @param {string} date - Transaction date
 * @param {string} type - Transaction type (Income/Expense)
 * @param {string} payment_mode - Payment mode (Bank/Cash)
 * @param {string} category - Transaction category
 * @param {string} description - Transaction description
 * @param {number} amount - Transaction amount
 */
function openEditModal(id, date, type, payment_mode, category, description, amount) {
    document.getElementById('expenseId').value = id;
    document.getElementById('editDate').value = date;
    document.getElementById('editCategory').value = category;
    document.getElementById('editDescription').value = description || '';
    document.getElementById('editAmount').value = amount;
    document.getElementById('editType').value = type;
    document.getElementById('editPayment').value = payment_mode;

    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

// ============================================
// ALERT FUNCTIONS
// ============================================

/**
 * Show alert message
 * @param {string} message - Alert message to display
 * @param {string} type - Bootstrap alert type (success, danger, warning, info)
 */
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show flash-message`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// ============================================
// TRANSACTION OPERATIONS
// ============================================

/**
 * Delete expense/transaction
 * @param {string} id - Transaction ID to delete
 */
function deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    fetch(`/delete/${id}`, {
        method: 'POST',
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showAlert('Transaction deleted successfully!', 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert('Error: ' + (data.message || 'Unknown error occurred.'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An unknown error occurred while deleting.', 'danger');
    });
}

/**
 * Update transaction
 * Sends updated transaction data to backend
 */
function updateTransaction() {
    const id = document.getElementById('expenseId').value;

    const updatedData = {
        category: document.getElementById('editCategory').value,
        amount: document.getElementById('editAmount').value,
        date: document.getElementById('editDate').value,
        description: document.getElementById('editDescription').value,
        payment_mode: document.getElementById('editPayment').value,
        type: document.getElementById('editType').value
    };

    // Validate required fields
    if (!updatedData.category || !updatedData.amount || !updatedData.date || 
        !updatedData.payment_mode || !updatedData.type) {
        showAlert('Please fill in all required fields!', 'warning');
        return;
    }

    fetch(`/edit/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
            modal.hide();
            showAlert('Transaction updated successfully!', 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showAlert('Failed to update transaction!', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating.', 'danger');
    });
}

// ============================================
// CHART INITIALIZATION
// ============================================

/**
 * Initialize all charts on page load
 */
function initializeCharts() {
    // Get data from JSON script tags
    const categories = JSON.parse(document.getElementById('categoriesData')?.textContent || '[]');
    const categoryValues = JSON.parse(document.getElementById('categoryValuesData')?.textContent || '[]');
    const months = JSON.parse(document.getElementById('monthsData')?.textContent || '[]');
    const monthlyExpenses = JSON.parse(document.getElementById('monthlyExpensesData')?.textContent || '[]');
    const monthlyIncome = JSON.parse(document.getElementById('monthlyIncomeData')?.textContent || '[]');
    const monthlySavings = JSON.parse(document.getElementById('monthlySavingsData')?.textContent || '[]');

    // Initialize Category Chart (Doughnut)
    initCategoryChart(categories, categoryValues);
    
    // Initialize Monthly Expense Trend Chart
    initExpenseTrendChart(months, monthlyExpenses);
    
    // Initialize Monthly Income Chart
    initIncomeChart(months, monthlyIncome);
    
    // Initialize Monthly Savings Chart
    initSavingsChart(months, monthlySavings);
}

/**
 * Initialize Category-wise Expenses Doughnut Chart
 * @param {Array} categories - Category labels
 * @param {Array} categoryValues - Category values
 */
function initCategoryChart(categories, categoryValues) {
    const categoryCtx = document.getElementById('categoryChart');
    
    if (typeof Chart !== 'undefined' && categoryCtx && categories.length > 0) {
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categories,
                datasets: [{
                    data: categoryValues,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: {
                            padding: 10,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return label + ': ₹' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize Monthly Expense Trend Line Chart
 * @param {Array} months - Month labels
 * @param {Array} monthlyExpenses - Monthly expense values
 */
function initExpenseTrendChart(months, monthlyExpenses) {
    const trendCtx = document.getElementById('trendChart');
    
    if (typeof Chart !== 'undefined' && trendCtx && months.length > 0) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Expenses (₹)',
                    data: monthlyExpenses,
                    fill: true,
                    backgroundColor: 'rgba(231, 74, 59, 0.1)',
                    borderColor: '#e74a3b',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#e74a3b',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Expenses: ₹' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize Monthly Income Line Chart
 * @param {Array} months - Month labels
 * @param {Array} monthlyIncome - Monthly income values
 */
function initIncomeChart(months, monthlyIncome) {
    const incomeCtx = document.getElementById('incomeChart');
    
    if (typeof Chart !== 'undefined' && incomeCtx && months.length > 0) {
        new Chart(incomeCtx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Income (₹)',
                    data: monthlyIncome,
                    fill: true,
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    borderColor: '#1cc88a',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#1cc88a',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Income: ₹' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize Monthly Savings Line Chart
 * @param {Array} months - Month labels
 * @param {Array} monthlySavings - Monthly savings values
 */
function initSavingsChart(months, monthlySavings) {
    const savingsCtx = document.getElementById('savingsChart');
    
    if (typeof Chart !== 'undefined' && savingsCtx && months.length > 0) {
        new Chart(savingsCtx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Savings (₹)',
                    data: monthlySavings,
                    fill: true,
                    backgroundColor: 'rgba(54, 185, 204, 0.1)',
                    borderColor: '#36b9cc',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#36b9cc',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Savings: ₹' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

// ============================================
// EVENT LISTENERS & INITIALIZATION
// ============================================

/**
 * Initialize all functionality when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all charts
    initializeCharts();

    // Save changes button event listener
    const saveChangesBtn = document.getElementById('saveChangesBtn');
    if (saveChangesBtn) {
        saveChangesBtn.addEventListener('click', updateTransaction);
    }

    // Auto-dismiss flash messages after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.flash-message .alert');
        alerts.forEach(alert => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (error) {
                console.error('Error closing alert:', error);
            }
        });
    }, 5000);

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Log successful initialization
    console.log('✅ Expense Tracker Dashboard initialized successfully!');
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Format currency for display
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format date for display
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Make functions globally available
window.openEditModal = openEditModal;
window.deleteExpense = deleteExpense;
window.updateTransaction = updateTransaction;
window.showAlert = showAlert;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;