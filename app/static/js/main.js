// Main JavaScript file for Digital Justice System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Handle notification read status
    const markAsReadButtons = document.querySelectorAll('.mark-notification-read');
    if (markAsReadButtons) {
        markAsReadButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const notificationId = this.getAttribute('data-notification-id');
                const url = `/communication/notifications/${notificationId}/mark-read`;
                
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update UI
                        const notificationItem = this.closest('.notification-item');
                        notificationItem.classList.remove('bg-light');
                        this.style.display = 'none';
                        
                        // Update notification count
                        const notificationCount = document.getElementById('notification-count');
                        if (notificationCount) {
                            const currentCount = parseInt(notificationCount.textContent);
                            if (currentCount > 0) {
                                notificationCount.textContent = currentCount - 1;
                                if (currentCount - 1 === 0) {
                                    notificationCount.style.display = 'none';
                                }
                            }
                        }
                    }
                })
                .catch(error => console.error('Error:', error));
            });
        });
    }

    // File upload preview
    const fileInput = document.getElementById('document_file');
    const filePreview = document.getElementById('file-preview');
    
    if (fileInput && filePreview) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (file.type.includes('image')) {
                        filePreview.innerHTML = `<img src="${e.target.result}" class="img-fluid" alt="Preview">`;
                    } else if (file.type.includes('pdf')) {
                        filePreview.innerHTML = `<div class="p-3 bg-light text-center"><i class="fas fa-file-pdf fa-3x text-danger"></i><p class="mt-2">${file.name}</p></div>`;
                    } else {
                        filePreview.innerHTML = `<div class="p-3 bg-light text-center"><i class="fas fa-file fa-3x text-primary"></i><p class="mt-2">${file.name}</p></div>`;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Payment amount calculation for fines
    const fineAmount = document.getElementById('fine-amount');
    const penaltyAmount = document.getElementById('penalty-amount');
    const totalAmount = document.getElementById('total-amount');
    
    if (fineAmount && penaltyAmount && totalAmount) {
        const fineValue = parseFloat(fineAmount.textContent);
        const penaltyValue = parseFloat(penaltyAmount.textContent);
        totalAmount.textContent = (fineValue + penaltyValue).toFixed(2);
    }

    // SOS Alert animation
    const sosButton = document.getElementById('sos-button');
    if (sosButton) {
        sosButton.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.add('pulse');
            setTimeout(() => {
                document.getElementById('sos-form').submit();
            }, 1000);
        });
    }

    // Dashboard charts (if Chart.js is included)
    if (typeof Chart !== 'undefined') {
        // Fine statistics chart
        const fineStatsCtx = document.getElementById('fineStatsChart');
        if (fineStatsCtx) {
            const fineStatsChart = new Chart(fineStatsCtx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Fines Issued',
                        data: [12, 19, 3, 5, 2, 3],
                        backgroundColor: 'rgba(63, 81, 181, 0.5)',
                        borderColor: 'rgba(63, 81, 181, 1)',
                        borderWidth: 1
                    }, {
                        label: 'Fines Paid',
                        data: [7, 11, 5, 8, 3, 7],
                        backgroundColor: 'rgba(76, 175, 80, 0.5)',
                        borderColor: 'rgba(76, 175, 80, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Dispute statistics chart
        const disputeStatsCtx = document.getElementById('disputeStatsChart');
        if (disputeStatsCtx) {
            const disputeStatsChart = new Chart(disputeStatsCtx, {
                type: 'pie',
                data: {
                    labels: ['Approved', 'Rejected', 'Pending'],
                    datasets: [{
                        data: [12, 19, 3],
                        backgroundColor: [
                            'rgba(76, 175, 80, 0.5)',
                            'rgba(244, 67, 54, 0.5)',
                            'rgba(255, 152, 0, 0.5)'
                        ],
                        borderColor: [
                            'rgba(76, 175, 80, 1)',
                            'rgba(244, 67, 54, 1)',
                            'rgba(255, 152, 0, 1)'
                        ],
                        borderWidth: 1
                    }]
                }
            });
        }
    }
});

// Helper function to get CSRF token from meta tag
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Function to show/hide password
function togglePasswordVisibility(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Function to confirm deletion
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Function to confirm action
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}
