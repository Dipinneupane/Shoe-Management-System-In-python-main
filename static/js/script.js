// Global Client Script for Happy Fit Shoe Store

document.addEventListener('DOMContentLoaded', () => {
    // 1. User Dropdown Menu Toggle
    const userBtn = document.querySelector('#user-btn');
    const userBox = document.querySelector('.header .header-2 .user-box');
    const navbar = document.querySelector('.header .header-2 .navbar');
    const menuBtn = document.querySelector('#menu-btn');

    if (userBtn && userBox) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userBox.classList.toggle('active');
            if (navbar) navbar.classList.remove('active');
        });
    }

    // 2. Mobile Menu Toggle
    if (menuBtn && navbar) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            navbar.classList.toggle('active');
            if (userBox) userBox.classList.remove('active');
        });
    }

    // 3. Dismiss flyouts when clicking outside
    document.addEventListener('click', (e) => {
        if (userBox && !userBox.contains(e.target) && userBtn && !userBtn.contains(e.target)) {
            userBox.classList.remove('active');
        }
        if (navbar && !navbar.contains(e.target) && menuBtn && !menuBtn.contains(e.target)) {
            navbar.classList.remove('active');
        }
    });

    // 4. Header Shadow on Scroll
    const header2 = document.querySelector('.header .header-2');
    window.addEventListener('scroll', () => {
        if (userBox) userBox.classList.remove('active');
        if (navbar) navbar.classList.remove('active');

        if (header2) {
            if (window.scrollY > 50) {
                header2.classList.add('active');
            } else {
                header2.classList.remove('active');
            }
        }
    });

    // 5. Auto-Dismiss Notifications
    const messages = document.querySelectorAll('.notification-container .message');
    messages.forEach((msg, idx) => {
        setTimeout(() => {
            msg.style.animation = 'fadeOutRight 0.35s ease forwards';
            setTimeout(() => {
                if (msg.parentElement) msg.remove();
            }, 350);
        }, 4500 + (idx * 500));
    });

    // 6. Scroll to top button
    const scrollTopBtn = document.querySelector('.scroll-top');
    if (scrollTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                scrollTopBtn.classList.add('active');
            } else {
                scrollTopBtn.classList.remove('active');
            }
        });

        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});

// Quantity Steppers (Safe global functions)
function incrementQuantity(element) {
    const input = element.parentElement ? element.parentElement.querySelector('input.qty, input[type="number"]') : element.previousElementSibling;
    if (input) {
        const max = parseInt(input.getAttribute('max')) || 999;
        const current = parseInt(input.value) || 1;
        if (current < max) {
            input.value = current + 1;
        }
    }
}

function decrementQuantity(element) {
    const input = element.parentElement ? element.parentElement.querySelector('input.qty, input[type="number"]') : element.nextElementSibling;
    if (input) {
        const min = parseInt(input.getAttribute('min')) || 1;
        const current = parseInt(input.value) || 1;
        if (current > min) {
            input.value = current - 1;
        }
    }
}