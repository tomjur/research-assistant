// Tab switching
function setActiveTab(btn) {
  const nav = btn.closest('.tab-nav');
  nav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// Sidebar active state
document.addEventListener('htmx:afterSwap', function(event) {
  if (event.target.id === 'main-panel') {
    // Mark the clicked sidebar item as active
    document.querySelectorAll('.task-item').forEach(item => item.classList.remove('active'));
    if (event.detail.elt && event.detail.elt.classList.contains('task-item')) {
      event.detail.elt.classList.add('active');
    }
  }
});
