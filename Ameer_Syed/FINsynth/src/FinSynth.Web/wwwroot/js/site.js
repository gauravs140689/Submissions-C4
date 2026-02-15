// FinSynth - Client-side interactions

window.FinSynth = {
    // File Upload Handler
    initializeFileUpload: function (dropZoneId, fileInputId) {
        const dropZone = document.getElementById(dropZoneId);
        const fileInput = document.getElementById(fileInputId);

        if (!dropZone || !fileInput) return;

        // Click to upload
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('dragover');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        }, false);
    },

    // Chart initialization (using Chart.js)
    createDebtPayoffChart: function (canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Remaining Debt',
                    data: data.balances,
                    borderColor: '#5AB5E5',
                    backgroundColor: 'rgba(90, 181, 229, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#b0b0b0',
                            callback: function (value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: '#2a2a2a'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#b0b0b0'
                        },
                        grid: {
                            color: '#2a2a2a'
                        }
                    }
                }
            }
        });
    },

    createIncomeExpenseChart: function (canvasId, income, expenses) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Available', 'Expenses'],
                datasets: [{
                    data: [income - expenses, expenses],
                    backgroundColor: ['#5AB5E5', '#D9B86A'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#b0b0b0',
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    },

    // Scroll chat to bottom
    scrollChatToBottom: function (chatId) {
        const chatMessages = document.getElementById(chatId);
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    },

    // Copy to clipboard
    copyToClipboard: function (text) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Copied to clipboard');
        });
    },

    // Format currency
    formatCurrency: function (value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    },

    // Toast notifications
    showToast: function (message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    console.log('FinSynth initialized');
});
