function hideLoader() {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        loader.classList.add('hidden');
        setTimeout(() => {
            loader.style.display = 'none';
        }, 600);
    }
}

function showLoader() {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        loader.style.display = 'flex';
        loader.classList.remove('hidden');
    }
}

window.addEventListener('load', function () {
    setTimeout(hideLoader, 300);
});

setTimeout(hideLoader, 8000);

document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('.navbar');
    const navbarBurger = document.querySelector('.navbar-burger');
    const navbarMenu = document.querySelector('.navbar-menu');

    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 100);

        const scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        document.querySelector('.progress-bar').style.width = `${scrollPercent}%`;
    });

    navbarBurger?.addEventListener('click', () => {
        navbarBurger.classList.toggle('is-active');
        navbarMenu.classList.toggle('is-active');
    });

    document.querySelectorAll('.navbar-item').forEach(item => {
        item.addEventListener('click', () => {
            navbarBurger?.classList.remove('is-active');
            navbarMenu?.classList.remove('is-active');
        });
    });

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            target?.scrollIntoView({behavior: 'smooth', block: 'start'});
        });
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
            }
        });
    }, {threshold: 0.1, rootMargin: '0px 0px -50px 0px'});

    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        observer.observe(element);
    });

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-target'));
                let current = 0;
                const increment = target / 100;
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                    }
                    counter.textContent = Math.ceil(current).toLocaleString();
                }, 20);
                statsObserver.unobserve(counter);
            }
        });
    }, {threshold: 0.5});

    document.querySelectorAll('.stats-counter').forEach(counter => {
        statsObserver.observe(counter);
    });

    const contactForm = document.getElementById('contactForm');

    contactForm?.addEventListener('submit', async function (e) {
        e.preventDefault();

        const submitButton = this.querySelector('button[type="submit"]');
        const originalContent = submitButton.innerHTML;

        const formData = new FormData(this);
        const {name, email, service, message, csrfmiddlewaretoken} = Object.fromEntries(formData.entries());

        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Sending...';
        submitButton.disabled = true;

        try {
            const response = await fetch('/contact/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfmiddlewaretoken
                },
                body: JSON.stringify({name, email, service, message})
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                submitButton.innerHTML = '<i class="fas fa-check mr-2"></i> Message Sent!';
                submitButton.style.background = 'linear-gradient(45deg, var(--accent), #00b894)';
                showNotification(result.message, 'success');

                setTimeout(() => {
                    submitButton.innerHTML = originalContent;
                    submitButton.style.background = 'linear-gradient(45deg, var(--secondary), #ff8c42)';
                    submitButton.disabled = false;
                    this.reset();
                }, 2000);
            } else {
                throw new Error(result.message || 'Submission failed.');
            }
        } catch (error) {
            submitButton.innerHTML = originalContent;
            submitButton.disabled = false;
            showNotification(error.message || 'An error occurred. Please try again later.', 'error');
            console.error('Contact form error:', error);
        }
    });

    function showNotification(message, type) {
        const container = document.getElementById('notificationContainer');
        const messageEl = container.querySelector('.notification-message');
        const iconEl = container.querySelector('.notification-icon');

        messageEl.textContent = message;
        iconEl.className = `fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} notification-icon`;

        container.className = `notification-container ${type}`;
        container.style.display = 'block';

        setTimeout(() => {
            closeNotification();
        }, 5000);
    }

    function closeNotification() {
        const container = document.getElementById('notificationContainer');
        container.classList.add('closing');

        setTimeout(() => {
            container.style.display = 'none';
            container.classList.remove('closing', 'success', 'error');
        }, 300);
    }

    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mousemove', function (e) {
            const rect = this.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;

            this.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(255, 107, 53, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%)`;
        });

        card.addEventListener('mouseleave', function () {
            this.style.background = 'rgba(255, 255, 255, 0.05)';
        });
    });

    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        const text = heroTitle.textContent;
        heroTitle.textContent = '';

        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                heroTitle.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };

        setTimeout(typeWriter, 1000);
    }

    const hero = document.querySelector('.hero');
    hero?.addEventListener('mousemove', (e) => {
        const {clientX, clientY} = e;
        const {innerWidth, innerHeight} = window;

        const xPercent = (clientX / innerWidth - 0.5) * 2;
        const yPercent = (clientY / innerHeight - 0.5) * 2;

        const heroTitle = document.querySelector('.hero-title');
        const heroSubtitle = document.querySelector('.hero-subtitle');

        if (heroTitle) heroTitle.style.transform = `translate(${xPercent * 10}px, ${yPercent * 10}px)`;
        if (heroSubtitle) heroSubtitle.style.transform = `translate(${xPercent * 5}px, ${yPercent * 5}px)`;
    });

    const partnersTrack = document.querySelector('.partners-track:not(.partners-no-animation)');
    if (partnersTrack) {
        partnersTrack.addEventListener('mouseenter', () => {
            partnersTrack.style.animationPlayState = 'paused';
        });

        partnersTrack.addEventListener('mouseleave', () => {
            partnersTrack.style.animationPlayState = 'running';
        });
    }
});

function openWhatsApp() {
    const message = encodeURIComponent("Hello! I'm interested in your printing services. Could you please provide more information?");
    const contactNumber = "{{ config.contact_number|default:'442012345678' }}".replace(/\s+/g, '');
    const whatsappURL = `https://wa.me/${contactNumber}?text=${message}`;
    window.open(whatsappURL, '_blank');
}

console.log('🎨 PeaShan Enterprises - Professional Printing Services Loaded Successfully!');