/**
 * Pollivu - Unified Application Script
 * Combines UI, Poll, and Chart logic into a namespaced structure.
 */

const Pollivu = {
    // ========================================================================
    // Core & UI Modules
    // ========================================================================
    UI: {
        init() {
            this.attachNavbarHandlers();

            this.attachModalHandlers();
            this.attachDropdownHandlers();
            this.attachSmoothScroll();
            this.attachFlashMessages();
            this.attachAOS(); // Animation on scroll
        },

        attachNavbarHandlers() {
            const navbarToggle = document.getElementById('navbar-toggle');
            const navbarMenu = document.getElementById('navbar-menu');

            if (navbarToggle && navbarMenu) {
                navbarToggle.addEventListener('click', () => {
                    navbarToggle.classList.toggle('active');
                    navbarMenu.classList.toggle('active');
                });

                document.addEventListener('click', (e) => {
                    if (!navbarToggle.contains(e.target) && !navbarMenu.contains(e.target)) {
                        navbarToggle.classList.remove('active');
                        navbarMenu.classList.remove('active');
                    }
                });
            }

            // Mobile Sidebar
            const mobileMenuBtn = document.getElementById('mobile-menu-btn');
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');

            if (mobileMenuBtn && sidebar && overlay) {
                mobileMenuBtn.addEventListener('click', () => {
                    sidebar.classList.add('open');
                    overlay.classList.add('active');
                });

                overlay.addEventListener('click', () => {
                    sidebar.classList.remove('open');
                    overlay.classList.remove('active');
                });
            }

            // Sidebar Toggle (Desktop) — removed, sidebar now uses CSS hover-expand
        },

        showToast(message, type = 'info') {
            // Delegate to the unified Toast system if available
            if (typeof Toast !== 'undefined' && Toast.show) {
                Toast.show(message, type);
                return;
            }

            // Fallback: create structured HTML matching toast.css
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                document.body.appendChild(container);
            }

            const icons = {
                success: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
                error: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
                info: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
            };

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-icon">${icons[type] || icons.info}</div>
                <div class="toast-message">${message}</div>
            `;

            container.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('show'));
            setTimeout(() => {
                toast.classList.remove('show');
                const cleanup = () => toast.remove();
                toast.addEventListener('transitionend', cleanup, { once: true });
                // Fallback: remove after 500ms if transitionend never fires
                setTimeout(cleanup, 500);
            }, 3000);
        },

        getCSRFToken() {
            const meta = document.querySelector('meta[name="csrf-token"]');
            return meta ? meta.content : '';
        },

        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showToast('Copied to clipboard!', 'success');
            } catch (error) {
                console.error('Failed to copy:', error);
                this.showToast('Failed to copy', 'error');
            }
        },

        attachModalHandlers() {
            // Generic close modal
            document.querySelectorAll('.modal-close, .modal-overlay').forEach(el => {
                el.addEventListener('click', () => {
                    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
                });
            });

            // Escape key closes active modals
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
                }
            });

            // Focus trapping inside active modals
            document.addEventListener('keydown', (e) => {
                if (e.key !== 'Tab') return;
                const modal = document.querySelector('.modal.active .modal-content');
                if (!modal) return;
                const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                if (focusable.length === 0) return;
                const first = focusable[0];
                const last = focusable[focusable.length - 1];
                if (e.shiftKey) {
                    if (document.activeElement === first) { e.preventDefault(); last.focus(); }
                } else {
                    if (document.activeElement === last) { e.preventDefault(); first.focus(); }
                }
            });
        },

        attachDropdownHandlers() {
            // Close all dropdowns when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.poll-actions-dropdown')) {
                    this.closeAllDropdowns();
                }
            });

            // Close dropdowns on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.closeAllDropdowns();
                }
            });
        },

        closeAllDropdowns() {
            document.querySelectorAll('.poll-actions-dropdown.active').forEach(d => {
                d.classList.remove('active');
            });
        },

        attachSmoothScroll() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    const href = this.getAttribute('href');
                    if (href === '#' || href.length < 2) return;
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                });
            });
        },

        attachFlashMessages() {
            document.querySelectorAll('.flash-message').forEach(message => {
                setTimeout(() => {
                    message.style.opacity = '0';
                    message.style.transform = 'translateY(-20px)';
                    setTimeout(() => message.remove(), 300);
                }, 5000);
            });
        },

        attachAOS() {
            const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) entry.target.classList.add('visible');
                });
            }, observerOptions);
            document.querySelectorAll('.animate-on-scroll, [data-aos]').forEach(el => observer.observe(el));
        }
    },

    // ========================================================================
    // Poll Management & Voting
    // ========================================================================
    Poll: {
        currentPollId: null,
        deleteTargetId: null,
        votingInstance: null,

        initVoting(pollId) {
            this.currentPollId = pollId;
            this.attachVoteHandlers();
            this.attachOptionHandlers();
        },

        initRealtime(pollId) {
            // Start realtime updates for results
            this.currentPollId = pollId;
            this.startPolling();

            document.addEventListener('visibilitychange', () => {
                if (document.hidden) this.stopPolling();
                else this.startPolling();
            });
        },

        attachOptionHandlers() {
            const options = document.querySelectorAll('.option-card');
            options.forEach(option => {
                // Skip already-voted options that don't allow vote change
                if (option.classList.contains('voted')) {
                    const radio = option.querySelector('input[type="radio"]');
                    if (radio && radio.disabled) return;
                }
                option.addEventListener('click', () => {
                    // Don't allow selection on voted cards without vote change
                    if (option.classList.contains('voted')) {
                        const radio = option.querySelector('input[type="radio"]');
                        if (radio && radio.disabled) return;
                    }
                    options.forEach(o => o.classList.remove('selected'));
                    option.classList.add('selected');
                    // auto select radio
                    const radio = option.querySelector('input[type="radio"]');
                    if (radio) radio.checked = true;
                });
            });
        },

        attachVoteHandlers() {
            const voteForm = document.getElementById('vote-form');
            if (voteForm) {
                voteForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.submitVote();
                });
            }
        },

        async submitVote() {
            if (!this.currentPollId) {
                Pollivu.UI.showToast('Poll not loaded. Please refresh the page.', 'error');
                return;
            }

            const selectedOption = document.querySelector('input[name="option"]:checked');
            if (!selectedOption) {
                Pollivu.UI.showToast('Please select an option', 'error');
                return;
            }

            const voteBtn = document.getElementById('vote-btn');
            if (voteBtn) {
                voteBtn.classList.add('loading');
                voteBtn.disabled = true;
            }

            try {
                const response = await fetch(`/poll/${this.currentPollId}/vote`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Pollivu.UI.getCSRFToken()
                    },
                    body: JSON.stringify({ option_id: selectedOption.value })
                });

                const data = await response.json();

                if (data.success) {
                    Pollivu.UI.showToast(data.message || 'Vote recorded!', 'success');
                    this.updateResultsDisplay(data.results, data.total_votes);
                    this.showVotedMessage();
                } else {
                    Pollivu.UI.showToast(data.error || 'Failed to submit vote', 'error');
                }
            } catch (error) {
                console.error('Vote error:', error);
                Pollivu.UI.showToast('Failed to submit vote', 'error');
            } finally {
                if (voteBtn) {
                    voteBtn.classList.remove('loading');
                    voteBtn.disabled = false;
                }
            }
        },

        updateResultsDisplay(results, totalVotes) {
            // Update total votes
            const total = document.getElementById('total-votes');
            if (total) total.textContent = totalVotes;

            // Should properly implement updating the results UI if on results page
            // Or simplified vote count on poll page
            results.forEach(res => {
                const el = document.querySelector(`.option-votes[data-option-id="${res.option_id}"]`);
                if (el) el.textContent = `${res.votes} votes`;
            });
        },

        showVotedMessage() {
            const container = document.querySelector('.poll-content');
            const form = document.getElementById('vote-form');
            const allowChange = form?.dataset.allowChange === 'true';

            let msg = document.querySelector('.voted-message');
            if (!msg && container) {
                msg = document.createElement('div');
                msg.className = 'voted-message';
                msg.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <path d="M22 4L12 14.01l-3-3"/>
                    </svg>
                    <span>You voted!${allowChange ? ' You can change your vote above.' : ''}</span>`;
                container.prepend(msg);
            }

            if (allowChange) {
                const btnText = document.querySelector('#vote-btn .btn-text');
                if (btnText) btnText.textContent = 'Change Vote';
            } else {
                // Vote is final — hide button and lock the options
                const voteBtn = document.getElementById('vote-btn');
                if (voteBtn) voteBtn.style.display = 'none';
                document.querySelectorAll('.option-radio').forEach(r => r.disabled = true);
                document.querySelectorAll('.option-card').forEach(c => c.style.pointerEvents = 'none');
            }

            // Add "View Full Results" link if not already present
            if (container && !document.querySelector('.view-results-link')) {
                const wrapper = document.createElement('div');
                wrapper.style.textAlign = 'center';
                wrapper.style.marginTop = '16px';
                const resultsLink = document.createElement('a');
                resultsLink.className = 'btn btn-secondary btn-lg view-results-link';
                resultsLink.href = `/poll/${this.currentPollId}/results`;
                resultsLink.textContent = 'View Full Results';
                wrapper.appendChild(resultsLink);
                container.appendChild(wrapper);
            }
        },

        // Management
        togglePublic(pollId) {
            fetch(`/poll/${pollId}/toggle-public`, {
                method: 'POST',
                headers: { 'X-CSRFToken': Pollivu.UI.getCSRFToken() }
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        Pollivu.UI.showToast(data.message, 'success');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        Pollivu.UI.showToast(data.error, 'error');
                    }
                })
                .catch(err => {
                    console.error('Toggle public error:', err);
                    Pollivu.UI.showToast('Network error. Please try again.', 'error');
                });
        },

        closePoll(pollId) {
            fetch(`/poll/${pollId}/close`, {
                method: 'POST',
                headers: { 'X-CSRFToken': Pollivu.UI.getCSRFToken() }
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        Pollivu.UI.showToast('Poll closed', 'success');
                        location.reload();
                    } else {
                        Pollivu.UI.showToast(data.error, 'error');
                    }
                })
                .catch(err => {
                    console.error('Close poll error:', err);
                    Pollivu.UI.showToast('Network error. Please try again.', 'error');
                });
        },

        reopenPoll(pollId) {
            fetch(`/poll/${pollId}/reopen`, {
                method: 'POST',
                headers: { 'X-CSRFToken': Pollivu.UI.getCSRFToken() }
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        Pollivu.UI.showToast('Poll reopened', 'success');
                        location.reload();
                    } else {
                        Pollivu.UI.showToast(data.error, 'error');
                    }
                })
                .catch(err => {
                    console.error('Reopen poll error:', err);
                    Pollivu.UI.showToast('Network error. Please try again.', 'error');
                });
        },

        confirmDelete(pollId) {
            this.deleteTargetId = pollId;
            const modal = document.getElementById('delete-modal');
            if (modal) modal.classList.add('active');
        },

        executeDelete() {
            if (!this.deleteTargetId) return;

            fetch(`/poll/${this.deleteTargetId}/delete`, {
                method: 'POST',
                headers: { 'X-CSRFToken': Pollivu.UI.getCSRFToken() }
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        Pollivu.UI.showToast('Poll deleted', 'success');
                        window.location.href = '/dashboard';
                    } else {
                        Pollivu.UI.showToast(data.error, 'error');
                    }
                })
                .catch(err => {
                    console.error('Delete poll error:', err);
                    Pollivu.UI.showToast('Network error. Please try again.', 'error');
                });
        },

        // Realtime
        pollingInterval: 30000,
        maxPollingInterval: 300000,
        basePollingInterval: 30000,

        async fetchStats() {
            try {
                const res = await fetch(`/api/poll/${this.currentPollId}/live_stats`);
                if (res.status === 429) {
                    // Backoff: double the interval, capped at maxPollingInterval
                    this.pollingInterval = Math.min(this.pollingInterval * 2, this.maxPollingInterval);
                    this.restartPolling();
                    return true; // keep polling active
                }
                if (!res.ok) return true;

                // Reset interval on success
                this.pollingInterval = this.basePollingInterval;

                const data = await res.json();
                if (data.success) {
                    Pollivu.Charts.updateBars(data.results);
                    const totalEl = document.getElementById('total-votes-count');
                    if (totalEl) totalEl.textContent = data.total_votes;
                }
                return true;
            } catch (e) {
                console.error(e);
                return true;
            }
        },

        startPolling() {
            if (this.timer) return;
            this.timer = setInterval(async () => {
                await this.fetchStats();
            }, this.pollingInterval);
        },

        stopPolling() {
            if (this.timer) { clearInterval(this.timer); this.timer = null; }
        },

        restartPolling() {
            this.stopPolling();
            this.startPolling();
        }
    },

    // ========================================================================
    // Charts & Visualization
    // ========================================================================
    Charts: {
        init() {
            if (document.querySelector('.result-bar')) {
                this.animateBars();
            }
        },

        animateBars() {
            document.querySelectorAll('.result-bar').forEach((bar, idx) => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.transition = 'width 0.8s ease-out';
                    bar.style.width = width;
                }, 100 + (idx * 50));
            });
        },

        updateBars(results) {
            results.forEach(res => {
                const item = document.querySelector(`.result-item[data-option-id="${res.option_id}"]`);
                if (!item) return;

                const bar = item.querySelector('.result-bar');
                const count = item.querySelector('.vote-count');
                const pct = item.querySelector('.percentage');

                if (bar) bar.style.width = `${res.percentage}%`;
                if (count) count.textContent = res.votes;
                if (pct) pct.textContent = `${res.percentage}%`;
            });
        }
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    Pollivu.UI.init();
    Pollivu.Charts.init();

    // Backwards compatibility bindings for legacy templates
    window.Pollivu = Pollivu;
    window.showToast = Pollivu.UI.showToast.bind(Pollivu.UI);
    window.getCSRFToken = Pollivu.UI.getCSRFToken.bind(Pollivu.UI);
});
