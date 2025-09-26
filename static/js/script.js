class PrintCraftApp {
    constructor() {
        this.navbar = null;
        this.navbarBurger = null;
        this.navbarMenu = null;
        this.observers = new Map();
        this.rafId = null;

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initAfterDOM());
            window.addEventListener('load', () => this.initAfterLoad());
        } else if (document.readyState === 'interactive') {
            this.initAfterDOM();
            window.addEventListener('load', () => this.initAfterLoad());
        } else {
            this.initAfterDOM();
            this.initAfterLoad();
        }
    }

    initAfterDOM() {
        this.cacheElements();
        this.initNavigation();
        this.initSmoothScrolling();
        this.initObservers();
        this.initFormHandling();
        this.initButtonEffects();
        this.initCardHoverEffects();
        this.initScrollProgress();
        this.initHeroParallax();
    }

    initAfterLoad() {
        this.removeLoader();
        this.initTypingEffect();
        this.initFloatingElements();
        this.logSuccess();
    }

    cacheElements() {
        [this.navbar, this.navbarBurger, this.navbarMenu] = [
            '.navbar',
            '.navbar-burger',
            '.navbar-menu'
        ].map(selector => document.querySelector(selector));
    }

    initNavigation() {
        if (!this.navbar || !this.navbarBurger || !this.navbarMenu) return;

        let ticking = false;
        const handleScroll = () => {
            if (ticking) return;

            this.rafId = requestAnimationFrame(() => {
                this.navbar.classList.toggle('scrolled', window.scrollY > 100);
                ticking = false;
            });
            ticking = true;
        };

        window.addEventListener('scroll', handleScroll, { passive: true });

        this.navbarBurger.addEventListener('click', () => {
            [this.navbarBurger, this.navbarMenu].forEach(el =>
                el.classList.toggle('is-active')
            );
        });

        document.querySelectorAll('.navbar-item').forEach(item => {
            item.addEventListener('click', () => {
                [this.navbarBurger, this.navbarMenu].forEach(el =>
                    el.classList.remove('is-active')
                );
            });
        });
    }

    initSmoothScrolling() {
        document.addEventListener('click', (e) => {
            const anchor = e.target.closest('a[href^="#"]');
            if (!anchor) return;

            e.preventDefault();
            document.querySelector(anchor.getAttribute('href'))
                ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    initObservers() {
        const observerConfigs = [
            {
                name: 'animate',
                selector: '.animate-on-scroll',
                options: { threshold: 0.1, rootMargin: '0px 0px -50px 0px' },
                callback: (entry) => {
                    entry.target.classList.add('animated');
                    return true; // Unobserve after animation
                }
            },
            {
                name: 'stats',
                selector: '.stats-counter',
                options: { threshold: 0.5 },
                callback: (entry) => {
                    this.animateCounter(entry.target);
                    return true; // Unobserve after animation
                }
            }
        ];

        observerConfigs.forEach(({ name, selector, options, callback }) => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && callback(entry)) {
                        observer.unobserve(entry.target);
                    }
                });
            }, options);

            document.querySelectorAll(selector).forEach(element => {
                observer.observe(element);
            });

            this.observers.set(name, observer);
        });

        this.initParallaxBackground();
    }

    initParallaxBackground() {
        const parallaxContainer = document.querySelector('.parallax-container');
        const parallaxBg = document.querySelector('.parallax-bg');

        if (!parallaxContainer || !parallaxBg) return;

        let ticking = false;
        const updateParallax = () => {
            const rect = parallaxContainer.getBoundingClientRect();
            const isVisible = rect.bottom >= 0 && rect.top <= window.innerHeight;

            if (isVisible) {
                const yPos = -(window.pageYOffset * 0.5);
                parallaxBg.style.transform = `translateY(${yPos}px)`;
            }
            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (ticking) return;
            this.rafId = requestAnimationFrame(updateParallax);
            ticking = true;
        }, { passive: true });
    }

    animateCounter(counter) {
        const target = parseInt(counter.dataset.target);
        const duration = 2000;
        const start = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.ceil(target * progress);

            counter.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    async initFormHandling() {
        const contactForm = document.getElementById('contactForm');
        if (!contactForm) return;

        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(contactForm);
            const submitButton = contactForm.querySelector('button[type="submit"]');

            this.updateButtonState(submitButton, 'loading');

            try {
                await new Promise(resolve => setTimeout(resolve, 1500));
                this.updateButtonState(submitButton, 'success');

                setTimeout(() => {
                    this.updateButtonState(submitButton, 'default');
                    contactForm.reset();
                }, 2000);
            } catch (error) {
                console.error('Form submission error:', error);
                this.updateButtonState(submitButton, 'default');
            }
        });
    }

    updateButtonState(button, state) {
        const states = new Map([
            ['loading', {
                html: '<i class="fas fa-spinner fa-spin"></i>&nbsp; Sending...',
                disabled: true
            }],
            ['success', {
                html: '<i class="fas fa-check"></i>&nbsp; Message Sent!',
                disabled: true,
                background: 'linear-gradient(45deg, var(--accent), #00b894)'
            }],
            ['default', {
                html: '<i class="fas fa-paper-plane"></i>&nbsp; Send Message',
                disabled: false,
                background: 'linear-gradient(45deg, var(--secondary), #ff8c42)'
            }]
        ]);

        const config = states.get(state);
        if (!config) return;

        Object.assign(button, {
            innerHTML: config.html,
            disabled: config.disabled
        });

        if (config.background) {
            button.style.background = config.background;
        }
    }

    initButtonEffects() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.cta-button');
            if (!button) return;

            this.createRippleEffect(button, e);
        });
    }

    createRippleEffect(button, event) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const { clientX, clientY } = event;
        const x = clientX - rect.left - size / 2;
        const y = clientY - rect.top - size / 2;

        Object.assign(ripple.style, {
            position: 'absolute',
            width: `${size}px`,
            height: `${size}px`,
            left: `${x}px`,
            top: `${y}px`,
            background: 'rgba(255, 255, 255, 0.3)',
            borderRadius: '50%',
            transform: 'scale(0)',
            animation: 'ripple 0.6s ease-out',
            pointerEvents: 'none'
        });

        Object.assign(button.style, {
            position: 'relative',
            overflow: 'hidden'
        });

        button.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }

    initCardHoverEffects() {
        document.querySelectorAll('.card').forEach(card => {
            const handleMouseMove = (e) => {
                const rect = card.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;

                card.style.background = `
                    radial-gradient(circle at ${x}% ${y}%,
                    rgba(255, 107, 53, 0.15) 0%,
                    rgba(255, 255, 255, 0.05) 100%)
                `;
            };

            const handleMouseLeave = () => {
                card.style.background = 'rgba(255, 255, 255, 0.05)';
            };

            card.addEventListener('mousemove', handleMouseMove);
            card.addEventListener('mouseleave', handleMouseLeave);
        });
    }

    initScrollProgress() {
        const progressBar = Object.assign(document.createElement('div'), {
            style: Object.assign(document.createElement('div').style, {
                position: 'fixed',
                top: '0',
                left: '0',
                width: '0%',
                height: '3px',
                background: 'linear-gradient(90deg, var(--secondary), var(--accent))',
                zIndex: '9998',
                transition: 'width 0.3s ease'
            })
        });

        document.body.appendChild(progressBar);

        let ticking = false;
        window.addEventListener('scroll', () => {
            if (ticking) return;

            this.rafId = requestAnimationFrame(() => {
                const { pageYOffset } = window;
                const { scrollHeight } = document.documentElement;
                const { innerHeight } = window;

                const scrollPercent = (pageYOffset / (scrollHeight - innerHeight)) * 100;
                progressBar.style.width = `${Math.min(scrollPercent, 100)}%`;
                ticking = false;
            });
            ticking = true;
        }, { passive: true });
    }

    initHeroParallax() {
        const hero = document.querySelector('.hero');
        const heroTitle = document.querySelector('.hero-title');
        const heroSubtitle = document.querySelector('.hero-subtitle');

        if (!hero || !heroTitle || !heroSubtitle) return;

        let ticking = false;
        hero.addEventListener('mousemove', (e) => {
            if (ticking) return;

            this.rafId = requestAnimationFrame(() => {
                const { clientX, clientY } = e;
                const { innerWidth, innerHeight } = window;

                const xPercent = (clientX / innerWidth - 0.5) * 2;
                const yPercent = (clientY / innerHeight - 0.5) * 2;

                heroTitle.style.transform = `translate(${xPercent * 10}px, ${yPercent * 10}px)`;
                heroSubtitle.style.transform = `translate(${xPercent * 5}px, ${yPercent * 5}px)`;
                ticking = false;
            });
            ticking = true;
        });
    }

    removeLoader() {
        const loader = document.getElementById('loader');
        if (!loader) return;

        setTimeout(() => {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 500);
        }, 500);
    }

    initTypingEffect() {
        const heroTitle = document.querySelector('.hero-title');
        if (!heroTitle) return;

        const text = heroTitle.textContent;
        heroTitle.textContent = '';

        const typeWriter = (i = 0) => {
            if (i < text.length) {
                heroTitle.textContent += text.charAt(i);
                setTimeout(() => typeWriter(i + 1), 100);
            }
        };

        setTimeout(() => typeWriter(), 1000);
    }

    initFloatingElements() {
        document.querySelectorAll('.floating').forEach((element, index) => {
            Object.assign(element.style, {
                animationDelay: `${index * 0.5}s`,
                animationDuration: `${3 + Math.random() * 2}s`
            });
        });
    }

    logSuccess() {
        console.log('🎨 PrintCraft Pro - Professional Printing Services Loaded Successfully!');
    }

    static openWhatsApp() {
        const message = encodeURIComponent("Hello! I'm interested in your printing services. Could you please provide more information?");
        const whatsappURL = `https://wa.me/254721284058?text=${message}`;
        window.open(whatsappURL, '_blank');
    }

    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();

        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
        }
    }
}

const printCraftApp = new PrintCraftApp();
window.openWhatsApp = PrintCraftApp.openWhatsApp;