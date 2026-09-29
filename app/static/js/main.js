// ==========================================================================
// Personal Finance Advisor Bot - Core Client Script
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // --- Mobile Sidebar Toggle ---
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => {
            sidebar.classList.remove('show');
        });
    }

    // --- Dropdown Management ---
    const demoBtn = document.getElementById('demoMenuBtn');
    const demoMenu = document.getElementById('demoMenu');

    if (demoBtn && demoMenu) {
        demoBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            demoMenu.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!demoMenu.contains(e.target) && e.target !== demoBtn) {
                demoMenu.classList.remove('show');
            }
        });
    }

    // --- Close Modals On Backdrop Click & Esc Key ---
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(m => closeModal(m.id));
        }
    });

    // --- Auto Dismiss Flash Alerts ---
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.style.transition = 'opacity 0.4s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        });
    }, 6000);
});

// Modal Helpers
function openModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Format numbers as Indian Rupee
function formatINR(val) {
    return '₹' + Number(val || 0).toLocaleString('en-IN', {
        maximumFractionDigits: 2,
        minimumFractionDigits: 0
    });
}
