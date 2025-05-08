// Toggle auth tabs (login/register)
document.addEventListener('DOMContentLoaded', function() {
    // Auth tab switching
    const tabs = document.querySelectorAll('.auth-tab');
    if (tabs) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Toggle forms
                const forms = document.querySelectorAll('.auth-form');
                forms.forEach(form => form.style.display = 'none');
                
                const formToShow = this.getAttribute('data-form');
                document.getElementById(formToShow).style.display = 'block';
            });
        });
    }

    // Job application handling
    const applyButtons = document.querySelectorAll('.apply-job');
    applyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const jobId = this.getAttribute('data-job-id');
            
            fetch(`/seeker/apply/${jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Application submitted successfully!');
                    window.location.href = '/seeker/applications';
                } else {
                    alert('Error: ' + data.message);
                }
            });
        });
    });

    // Initialize tooltips
    const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener('mouseenter', showTooltip);
        trigger.addEventListener('mouseleave', hideTooltip);
    });
});

function showTooltip(e) {
    const tooltipText = this.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    
    document.body.appendChild(tooltip);
    
    const rect = this.getBoundingClientRect();
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
    tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
    
    this.tooltip = tooltip;
}

function hideTooltip() {
    if (this.tooltip) {
        this.tooltip.remove();
    }
}

// Flash message auto-hide
setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        msg.style.opacity = '0';
        setTimeout(() => msg.remove(), 500);
    });
}, 3000);