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
            const container = document.getElementById('toast-container');
            if (!container) return;

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;

            container.appendChild(toast);
            setTimeout(() => toast.classList.add('show'), 100);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
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
        },

        attachDropdownHandlers() {
            // If any global dropdown handling is needed
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
                option.addEventListener('click', () => {
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
                });
        },

        // Realtime
        async fetchStats() {
            try {
                const res = await fetch(`/api/poll/${this.currentPollId}/live_stats`);
                if (res.status === 429) return false;
                if (!res.ok) return true;

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
                const cont = await this.fetchStats();
                if (!cont) this.stopPolling();
            }, 30000);
        },

        stopPolling() {
            if (this.timer) { clearInterval(this.timer); this.timer = null; }
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
