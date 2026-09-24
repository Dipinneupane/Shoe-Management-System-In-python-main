// Admin Dashboard & Management Script

document.addEventListener('DOMContentLoaded', () => {
    const navbar = document.querySelector('.header .navbar');
    const accountBox = document.querySelector('.header .account-box');
    const menuBtn = document.querySelector('#menu-btn');
    const userBtn = document.querySelector('#user-btn');

    if (menuBtn && navbar) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            navbar.classList.toggle('active');
            if (accountBox) accountBox.classList.remove('active');
        });
    }

    if (userBtn && accountBox) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            accountBox.classList.toggle('active');
            if (navbar) navbar.classList.remove('active');
        });
    }

    document.addEventListener('click', (e) => {
        if (accountBox && !accountBox.contains(e.target) && userBtn && !userBtn.contains(e.target)) {
            accountBox.classList.remove('active');
        }
        if (navbar && !navbar.contains(e.target) && menuBtn && !menuBtn.contains(e.target)) {
            navbar.classList.remove('active');
        }
    });

    window.addEventListener('scroll', () => {
        if (navbar) navbar.classList.remove('active');
        if (accountBox) accountBox.classList.remove('active');
    });

    // Auto-dismiss notifications
    const messages = document.querySelectorAll('.notification-container .message');
    messages.forEach((msg, idx) => {
        setTimeout(() => {
            msg.style.animation = 'fadeOutRight 0.35s ease forwards';
            setTimeout(() => {
                if (msg.parentElement) msg.remove();
            }, 350);
        }, 4500 + (idx * 500));
    });
});