// ABC College Portal – main.js

// Auto-dismiss alerts after 4 seconds
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 4000);
});

// Confirm delete actions
document.querySelectorAll('[data-confirm]').forEach(btn => {
  btn.addEventListener('click', e => {
    if (!confirm(btn.dataset.confirm || 'Are you sure?')) e.preventDefault();
  });
});

// Semester ribbon: mark active from URL param
const urlParams = new URLSearchParams(window.location.search);
const activeSem = urlParams.get('sem');
if (activeSem) {
  document.querySelectorAll('.sem-btn').forEach(btn => {
    if (btn.textContent.trim() === `Sem ${activeSem}`) btn.classList.add('active');
  });
}
