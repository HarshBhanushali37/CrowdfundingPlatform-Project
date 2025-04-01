document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handle search form
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('searchInput');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.classList.add('is-invalid');
            }
        });
    }
    
    // Confirm delete actions
    const confirmDeleteButtons = document.querySelectorAll('.confirm-delete');
    confirmDeleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialize any charts on the page
    initializeCharts();
});

// Function to initialize charts if needed
function initializeCharts() {
    // Check if we're on a page with campaign detail
    const campaignChartElements = document.querySelectorAll('[id^="progressChart-"]');
    
    campaignChartElements.forEach(element => {
        const campaignId = element.getAttribute('data-campaign-id');
        const currentAmount = parseFloat(element.getAttribute('data-current'));
        const goalAmount = parseFloat(element.getAttribute('data-goal'));
        
        if (typeof initDonationProgressChart === 'function') {
            initDonationProgressChart(campaignId, currentAmount, goalAmount);
        }
    });
    
    // For admin dashboard timeline chart
    const timelineChart = document.getElementById('donationsTimelineChart');
    if (timelineChart && typeof initDonationTimelineChart === 'function') {
        const labels = JSON.parse(timelineChart.getAttribute('data-labels') || '[]');
        const values = JSON.parse(timelineChart.getAttribute('data-values') || '[]');
        
        initDonationTimelineChart('donationsTimelineChart', labels, values);
    }
    
    // For admin dashboard category distribution
    const categoryChart = document.getElementById('categoriesChart');
    if (categoryChart && typeof initCategoryChart === 'function') {
        const categories = JSON.parse(categoryChart.getAttribute('data-categories') || '[]');
        const counts = JSON.parse(categoryChart.getAttribute('data-counts') || '[]');
        
        initCategoryChart('categoriesChart', categories, counts);
    }
}
