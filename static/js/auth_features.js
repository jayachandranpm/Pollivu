/**
 * Pollivu - Auth Features
 * Handles password toggle and validation
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Password Visibility Toggle
    const toggleButtons = document.querySelectorAll('.password-toggle');

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = btn.querySelector('svg');

            if (input.type === 'password') {
                input.type = 'text';
                // Switch to Eye Off icon
                icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
            } else {
                input.type = 'password';
                // Switch to Eye icon
                icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
            }
        });
    });

    // 2. Real-time Password Validation (Registration Page)
    const passwordInput = document.getElementById('password');
    const requirements = {
        length: document.querySelector('[data-requirement="length"]'),
        case: document.querySelector('[data-requirement="case"]'),
        special: document.querySelector('[data-requirement="special"]')
    };

    if (passwordInput && requirements.length) { // Only run if requirements exist (Registration page)
        passwordInput.addEventListener('input', () => {
            const val = passwordInput.value;

            // Check Length (>= 8)
            if (val.length >= 8) {
                requirements.length.classList.add('valid');
            } else {
                requirements.length.classList.remove('valid');
            }

            // Check Case (Upper & Lower)
            if (/[a-z]/.test(val) && /[A-Z]/.test(val)) {
                requirements.case.classList.add('valid');
            } else {
                requirements.case.classList.remove('valid');
            }

            // Check Number & Special
            if (/[0-9]/.test(val) && /[!@#$%^&*(),.?":{}|<>]/.test(val)) {
                requirements.special.classList.add('valid');
            } else {
                requirements.special.classList.remove('valid');
            }
        });
    }
});
