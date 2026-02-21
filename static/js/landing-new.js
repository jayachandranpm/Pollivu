/**
 * Pollivu - Main JavaScript
 * Handles interactivity: mobile menu, smooth scrolling, and scroll animations
 */

// ==========================================================================
// Mobile Menu Toggle
// ==========================================================================

function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    const menuIcon = document.querySelector('.menu-icon');
    const closeIcon = document.querySelector('.close-icon');

    if (!mobileMenu || !menuIcon || !closeIcon) return;

    if (mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.remove('hidden');
        menuIcon.classList.add('hidden');
        closeIcon.classList.remove('hidden');
    } else {
        mobileMenu.classList.add('hidden');
        mobileMenu.style.removeProperty('display');
        menuIcon.classList.remove('hidden');
        closeIcon.classList.add('hidden');
    }
}

// ==========================================================================
// Smooth Scroll to Section
// ==========================================================================

function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        const header = document.getElementById('header');
        const headerOffset = header ? header.offsetHeight + 16 : 80;
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }

    // Close mobile menu if open
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
        toggleMobileMenu();
    }
}

// ==========================================================================
// Scroll-Based Animations (Intersection Observer)
// ==========================================================================

function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Get the delay from CSS custom property if set
                const delay = getComputedStyle(entry.target).getPropertyValue('--delay') || '0s';
                const delayMs = parseFloat(delay) * 1000;

                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, delayMs);

                // Unobserve after animation triggers
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// ==========================================================================
// Header Scroll Effect
// ==========================================================================

function initHeaderScrollEffect() {
    const header = document.getElementById('header');
    if (!header) return;

    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;

        if (currentScrollY > 100) {
            header.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.boxShadow = 'none';
        }

        lastScrollY = currentScrollY;
    }, { passive: true });
}

// ==========================================================================
// Dynamic Year in Footer
// ==========================================================================

function setCurrentYear() {
    const yearElement = document.getElementById('year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
}

// ==========================================================================
// Initialize on DOM Ready
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initHeaderScrollEffect();
    setCurrentYear();
});

// ==========================================================================
// Reduce Motion Detection
// ==========================================================================

// Check for reduced motion preference
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

if (prefersReducedMotion.matches) {
    // If user prefers reduced motion, make all elements visible immediately
    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        element.classList.add('visible');
    });
}

// Listen for changes in motion preference
prefersReducedMotion.addEventListener('change', (event) => {
    if (event.matches) {
        document.querySelectorAll('.animate-on-scroll').forEach(element => {
            element.classList.add('visible');
        });
    }
});
