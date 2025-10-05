const NOTIFICATION_TIMEOUT = 5000;
const DEBOUNCE_DELAY = 300;
const GALLERY_PER_PAGE = 9;
const INTERSECTION_ROOT_MARGIN = '200px';

const showNotification = (message, type = 'info') => {
    document.querySelectorAll('.notification').forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message"></span>
            <button class="notification-close">&times;</button>
        </div>
    `;

    notification.querySelector('.notification-message').textContent = message;
    document.body.appendChild(notification);

    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => notification.remove());

    setTimeout(() => notification.parentNode && notification.remove(), NOTIFICATION_TIMEOUT);
};

document.addEventListener('DOMContentLoaded', () => {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay?.classList.add('hidden');

    initMobileMenu();
    initTypewriter();

    initContactForm();
    initSmoothScroll();

    if (document.getElementById('galleryPreview')) {
        initGalleryPreview();
    }

    if (document.getElementById('galleryGrid')) {
        initGallery();
    }
});

const initGalleryPreview = () => {
    const galleryPreview = document.getElementById('galleryPreview');
    if (!galleryPreview) return;

    galleryPreview.addEventListener('click', (e) => {
        if (e.target.closest('.gallery-item')) {
            showNotification('This is a preview! Visit the full gallery to see detailed images.', 'info');
        }
    });
};

const initContactForm = () => {
    const form = document.getElementById('contactForm');
    if (!form) return;

    const submitBtn = form.querySelector('button[type="submit"]');
    const validators = {
        name: (value) => value.trim() !== '',
        email: (value) => /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/.test(value.trim()),
        message: (value) => value.trim() !== ''
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const fields = ['name', 'email', 'message'];
        
        const isValid = fields.every(fieldId => {
            const field = document.getElementById(fieldId);
            const fieldGroup = field.closest('.form-group');
            const valid = validators[fieldId](field.value);
            
            fieldGroup.classList.toggle('error', !valid);
            return valid;
        });

        if (!isValid) return;

        try {
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Sending...';
            submitBtn.disabled = true;

            const response = await fetch('/contact/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();

            if (data.success) {
                showNotification('Thank you for your message! We will get back to you soon.', 'success');
                form.reset();
            } else {
                showNotification(data.message || 'There was an issue sending your message. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            showNotification('There was an issue sending your message. Please try again.', 'error');
        } finally {
            submitBtn.textContent = submitBtn.originalText || 'Send Message';
            submitBtn.disabled = false;
        }
    });

    form.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('input', () => {
            input.closest('.form-group').classList.remove('error');
        });
    });
};

const initMobileMenu = () => {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMenuBtn = document.getElementById('close-menu');

    if (!mobileMenuBtn || !mobileMenu) return;

    const toggleMobileMenu = () => {
        const isActive = mobileMenu.classList.toggle('active');
        document.body.style.overflow = isActive ? 'hidden' : 'auto';
    };

    mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    closeMenuBtn?.addEventListener('click', toggleMobileMenu);

    document.querySelectorAll('.mobile-nav-link a').forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.remove('active');
            document.body.style.overflow = 'auto';
        });
    });
};

const initSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
};

class Lightbox {
    constructor() {
        this.currentIndex = 0;
        this.galleryItems = [];
        this.elements = {
            lightbox: document.getElementById('lightbox'),
            img: document.getElementById('lightbox-img'),
            title: document.getElementById('lightbox-title'),
            desc: document.getElementById('lightbox-desc'),
            category: document.getElementById('lightbox-category'),
            close: document.getElementById('close-lightbox'),
            prev: document.getElementById('prev-btn'),
            next: document.getElementById('next-btn')
        };
    }

    setItems(items) {
        this.galleryItems = items;
    }

    open(index) {
        if (this.galleryItems.length === 0 || index < 0 || index >= this.galleryItems.length) return;

        const item = this.galleryItems[index];
        const { img, title, desc, category, lightbox } = this.elements;

        if (img) {
            img.src = item.fullImage;
            img.onerror = function() {
                this.onerror = null;
                this.src = '/static/default.png';
            };
        }

        if (title) title.textContent = item.title;
        if (desc) desc.textContent = item.description || 'Premium printing project showcasing our quality work.';
        
        if (category) {
            const hasTags = Array.isArray(item.tags) && item.tags.length > 0;
            if (hasTags) {
                category.innerHTML = item.tags.map(t => `<span class="tag-pill">${t}</span>`).join('');
                category.style.display = 'block';
            } else {
                category.innerHTML = '';
                category.style.display = 'none';
            }
        }

        this.currentIndex = index;
        this.updateNavButtons();

        if (lightbox) {
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        const { lightbox } = this.elements;
        if (lightbox) {
            lightbox.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    }

    goToPrev() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.open(this.currentIndex);
        }
    }

    goToNext() {
        if (this.currentIndex < this.galleryItems.length - 1) {
            this.currentIndex++;
            this.open(this.currentIndex);
        }
    }

    updateNavButtons() {
        const { prev, next } = this.elements;
        if (prev) prev.disabled = this.currentIndex === 0;
        if (next) next.disabled = this.currentIndex === this.galleryItems.length - 1;
    }

    setupEventListeners() {
        const { close, lightbox, prev, next } = this.elements;

        close?.addEventListener('click', () => this.close());
        lightbox?.addEventListener('click', (e) => {
            if (e.target === lightbox) this.close();
        });
        prev?.addEventListener('click', () => this.goToPrev());
        next?.addEventListener('click', () => this.goToNext());

        document.addEventListener('keydown', (e) => {
            if (!lightbox?.classList.contains('active')) return;

            const actions = {
                'Escape': () => this.close(),
                'ArrowLeft': () => this.goToPrev(),
                'ArrowRight': () => this.goToNext()
            };

            actions[e.key]?.();
        });
    }
}

const initGallery = () => {
    const API_BASE_URL = window.location.origin;
    
    const state = {
        currentPage: 1,
        currentFilters: { search: '', tags: [] },
        isLoading: false,
        hasMorePages: true,
        lastItemObserver: null,
        lastObservedItem: null
    };

    const elements = {
        galleryGrid: document.getElementById('galleryGrid'),
        filterButtons: document.querySelectorAll('.filter-btn'),
        clearFiltersBtn: document.getElementById('clear-filters'),
        searchInput: document.getElementById('search-input'),
        mobileSearchInput: document.getElementById('mobile-search-input'),
        loadingSpinner: document.getElementById('loadingSpinner'),
        noResults: document.getElementById('noResults')
    };

    if (!elements.galleryGrid) return;

    const lightbox = new Lightbox();
    lightbox.setupEventListeners();

    const createGalleryItem = (item) => {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item';
        galleryItem.dataset.category = item.tags.join(' ');
        galleryItem.dataset.itemId = item.id;

        const tagsHtml = item.tags?.length ? `<div class="tags">${item.tags.map(t => `<span class='tag-pill'>${t}</span>`).join('')}</div>` : '';
        
        galleryItem.innerHTML = `
            <img src="${item.thumbnail}" alt="${item.title}" class="gallery-img" loading="lazy"
                  onerror="this.onerror=null; this.src='/static/default.png';">
            <div class="gallery-overlay">
                <h3>${item.title}</h3>
                <p>${item.description || 'Premium printing project showcasing our quality work.'}</p>
                ${tagsHtml}
                <div class="view-btn">
                    <i class="fas fa-expand"></i>
                </div>
            </div>
        `;

        return galleryItem;
    };

    const showLoadingState = () => elements.loadingSpinner && (elements.loadingSpinner.style.display = 'block');
    const hideLoadingState = () => elements.loadingSpinner && (elements.loadingSpinner.style.display = 'none');
    
    const showNoResults = () => {
        if (elements.noResults) elements.noResults.style.display = 'block';
        hideLoadingState();
    };
    
    const hideNoResults = () => elements.noResults && (elements.noResults.style.display = 'none');

    const fetchGalleryData = async (page = 1, append = false) => {
        if (state.isLoading) return;

        state.isLoading = true;
        if (!append) showLoadingState();

        try {
            const params = new URLSearchParams({
                page,
                per_page: GALLERY_PER_PAGE,
                search: state.currentFilters.search
            });

            if (state.currentFilters.tags.length) {
                params.set('tags', state.currentFilters.tags);
            }

            const response = await fetch(`${API_BASE_URL}/api/gallery/?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();

            if (data.success) {
                state.hasMorePages = data.pagination.has_next;
                state.currentPage = data.pagination.current_page;

                if (append) {
                    // Append new items to lightbox so newly loaded items are navigable
                    lightbox.setItems([...(lightbox.galleryItems || []), ...data.items]);
                    renderGalleryItems(data.items, true);
                } else {
                    // Initial page load or filters changed: replace items
                    lightbox.setItems(data.items);
                    renderGalleryItems(data.items, false);
                }
            } else {
                throw new Error(data.message || 'Failed to fetch gallery data');
            }
        } catch (error) {
            console.error('Error fetching gallery data:', error);
            if (!append) {
                console.error('Failed to load gallery items. Please check your connection and try again.');
            }
        } finally {
            state.isLoading = false;
            hideLoadingState();
        }
    };

    const renderGalleryItems = (items, append = false) => {
        if (!append) elements.galleryGrid.innerHTML = '';

        if (items.length === 0) {
            showNoResults();
            return;
        }

        hideNoResults();

        const fragment = document.createDocumentFragment();
        items.forEach(item => fragment.appendChild(createGalleryItem(item)));
        elements.galleryGrid.appendChild(fragment);

        if (state.lastItemObserver) {
            if (state.lastObservedItem) {
                state.lastItemObserver.unobserve(state.lastObservedItem);
            }
            state.lastObservedItem = elements.galleryGrid.lastElementChild;
            state.lastObservedItem && state.lastItemObserver.observe(state.lastObservedItem);
        }
    };

    const applyFilters = () => {
        state.currentPage = 1;
        fetchGalleryData(1, false);
    };

    const toggleFilter = (category) => {
        if (category === 'all') {
            state.currentFilters.tags = [];
        } else {
            const tagIndex = state.currentFilters.tags.indexOf(category);
            tagIndex > -1 
                ? state.currentFilters.tags.splice(tagIndex, 1)
                : state.currentFilters.tags.push(category);
        }

        elements.filterButtons.forEach(btn => {
            const isAll = btn.dataset.filter === 'all';
            btn.classList.toggle('active', isAll 
                ? state.currentFilters.tags.length === 0
                : state.currentFilters.tags.includes(btn.dataset.filter)
            );
        });

        applyFilters();
    };

    const clearFilters = () => {
        state.currentFilters.tags = [];
        state.currentFilters.search = '';

        elements.filterButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === 'all');
        });

        if (elements.searchInput) elements.searchInput.value = '';
        if (elements.mobileSearchInput) elements.mobileSearchInput.value = '';

        applyFilters();
    };

    const debounce = (func, wait) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    };

    const performSearch = (query) => {
        state.currentFilters.search = query;
        applyFilters();
    };

    const debouncedSearch = debounce(performSearch, DEBOUNCE_DELAY);

    const setupInfiniteScroll = () => {
        state.lastItemObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && !state.isLoading && state.hasMorePages) {
                fetchGalleryData(state.currentPage + 1, true);
            }
        }, {
            rootMargin: INTERSECTION_ROOT_MARGIN,
            threshold: 0.1
        });
    };

    elements.galleryGrid.addEventListener('click', (e) => {
        const galleryItem = e.target.closest('.gallery-item');
        if (!galleryItem) return;

        const itemId = parseInt(galleryItem.dataset.itemId);
        const index = lightbox.galleryItems.findIndex(i => i.id === itemId);

        if (index !== -1) lightbox.open(index);
    });

    elements.filterButtons.forEach(button => {
        button.addEventListener('click', () => toggleFilter(button.dataset.filter));
    });

    elements.clearFiltersBtn?.addEventListener('click', clearFilters);

    const syncSearchInputs = (sourceInput, targetInput) => (e) => {
        debouncedSearch(e.target.value);
        if (targetInput) targetInput.value = e.target.value;
    };

    elements.searchInput?.addEventListener('input', syncSearchInputs(elements.searchInput, elements.mobileSearchInput));
    elements.mobileSearchInput?.addEventListener('input', syncSearchInputs(elements.mobileSearchInput, elements.searchInput));

    fetchGalleryData(1, false);
    setupInfiniteScroll();
};

const initTypewriter = () => {
    try {
        const heading = document.querySelector('.hero-content h1');
        if (!heading || heading.dataset.typed === '1') return;

        heading.dataset.typed = '1';
        const fullText = (heading.textContent || '').trim();
        if (!fullText) return;

        heading.textContent = '';
        const caret = document.createElement('span');
        caret.className = 'typewriter-caret';
        heading.appendChild(caret);

        let i = 0;
        const TYPE_SPEED = 60;
        const START_DELAY = 300;

        const typeNext = () => {
            if (i < fullText.length) {
                caret.insertAdjacentText('beforebegin', fullText.charAt(i));
                i++;
                setTimeout(typeNext, TYPE_SPEED);
            }
        };

        setTimeout(typeNext, START_DELAY);
    } catch (e) {
        console.warn('Typewriter init failed:', e);
    }
};