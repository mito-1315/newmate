// Test API endpoints
console.log('Testing API endpoints...');

// Test health check
fetch('/')
  .then(response => response.json())
  .then(data => console.log('Health check:', data))
  .catch(error => console.error('Health check error:', error));

// Test analytics
fetch('/analytics/verification-stats')
  .then(response => response.json())
  .then(data => console.log('Analytics:', data))
  .catch(error => console.error('Analytics error:', error));

// Test reviews
fetch('/reviews')
  .then(response => response.json())
  .then(data => console.log('Reviews:', data))
  .catch(error => console.error('Reviews error:', error));
