// Constants
const NOTIFICATION_TIMEOUT = 5000;
const DEBOUNCE_DELAY = 300;
const GALLERY_PER_PAGE = 9;
const INTERSECTION_ROOT_MARGIN = '200px';

// Clean, simple notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message"></span>
            <button class="notification-close">&times;</button>
        </div>
    `;

    // Set message using textContent to prevent XSS
    const messageSpan = notification.querySelector('.notification-message');
    messageSpan.textContent = message;

    // Add to page
    document.body.appendChild(notification);

    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');

    closeBtn.addEventListener('click', () => {
        notification.remove();
    });

    // Auto remove after timeout
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, NOTIFICATION_TIMEOUT);
}

// DOM Content Load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired');
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }

    // Initialize mobile menu on all pages
    initMobileMenu();

    // Typewriter effect for hero title (safe no-op if element missing)
    initTypewriter();

    // Initialize all sections based on current page
    if (document.getElementById('galleryPreview')) {
        console.log('On index.html, initializing index functions');
        // We're on index.html
        initGalleryPreview();
        initContactForm();
        initSmoothScroll();
    }

    if (document.getElementById('galleryGrid')) {
        console.log('On gallery.html, initializing gallery');
        // We're on gallery.html
        initGallery();
    }
});

// Gallery Preview (for index.html)
function initGalleryPreview() {
    const galleryPreview = document.getElementById('galleryPreview');
    if (!galleryPreview) return;

    // Use event delegation for gallery items
    galleryPreview.addEventListener('click', (e) => {
        if (e.target.closest('.gallery-item')) {
            showNotification('This is a preview! Visit the full gallery to see detailed images.', 'info');
        }
    });
}



// Contact Form Validation (for index.html)
function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    const submitBtn = form.querySelector('button[type="submit"]');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        let isValid = true;
        const formData = new FormData(form);

        // Name validation
        const name = document.getElementById('name');
        const nameGroup = name.closest('.form-group');
        if (name.value.trim() === '') {
            nameGroup.classList.add('error');
            isValid = false;
        } else {
            nameGroup.classList.remove('error');
        }

        // Email validation
        const email = document.getElementById('email');
        const emailGroup = email.closest('.form-group');
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value.trim())) {
            emailGroup.classList.add('error');
            isValid = false;
        } else {
            emailGroup.classList.remove('error');
        }

        // Message validation
        const message = document.getElementById('message');
        const messageGroup = message.closest('.form-group');
        if (message.value.trim() === '') {
            messageGroup.classList.add('error');
            isValid = false;
        } else {
            messageGroup.classList.remove('error');
        }

        if (isValid) {
            try {
                // Show loading state
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Sending...';
                submitBtn.disabled = true;

                // Send form data to Django backend
                const response = await fetch('/gallery/contact/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Show success message
                    showNotification('Thank you for your message! We will get back to you soon.', 'success');
                    form.reset();
                } else {
                    // Show error message
                    showNotification(data.message || 'There was an issue sending your message. Please try again.', 'error');
                }

            } catch (error) {
                console.error('Error submitting form:', error);
                showNotification('There was an issue sending your message. Please try again.', 'error');
            } finally {
                // Reset button state
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        }
    });

    // Remove error on input
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            input.closest('.form-group').classList.remove('error');
        });
    });
}




// Mobile Menu (shared between both pages)
function initMobileMenu() {
    console.log('initMobileMenu called');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMenuBtn = document.getElementById('close-menu');

    console.log('mobileMenuBtn:', mobileMenuBtn);
    console.log('mobileMenu:', mobileMenu);
    console.log('closeMenuBtn:', closeMenuBtn);

    if (!mobileMenuBtn || !mobileMenu) {
        console.log('Mobile menu elements not found, skipping');
        return;
    }

    const toggleMobileMenu = () => {
        console.log('Toggling mobile menu');
        mobileMenu.classList.toggle('active');
        document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : 'auto';
        console.log('Menu active:', mobileMenu.classList.contains('active'));
    };

    mobileMenuBtn.addEventListener('click', () => {
        console.log('Mobile menu button clicked');
        toggleMobileMenu();
    });

    if (closeMenuBtn) {
        closeMenuBtn.addEventListener('click', () => {
            console.log('Close menu button clicked');
            toggleMobileMenu();
        });
    }

    // Close menu when clicking a link
    document.querySelectorAll('.mobile-nav-link a').forEach(link => {
        link.addEventListener('click', () => {
            console.log('Mobile nav link clicked, closing menu');
            mobileMenu.classList.remove('active');
            document.body.style.overflow = 'auto';
        });
    });
}

// Smooth Scroll (for index.html)
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// Lightbox class for gallery images
class Lightbox {
    constructor() {
        this.currentIndex = 0;
        this.galleryItems = [];
        this.lightbox = document.getElementById('lightbox');
        this.lightboxImg = document.getElementById('lightbox-img');
        this.lightboxTitle = document.getElementById('lightbox-title');
        this.lightboxDesc = document.getElementById('lightbox-desc');
        this.lightboxCategory = document.getElementById('lightbox-category');
        this.closeLightbox = document.getElementById('close-lightbox');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
    }

    setItems(items) {
        this.galleryItems = items;
    }

    open(index) {
        if (this.galleryItems.length === 0 || index < 0 || index >= this.galleryItems.length) {
            return;
        }

        const item = this.galleryItems[index];

        if (this.lightboxImg) {
            this.lightboxImg.src = item.fullImage;
            this.lightboxImg.onerror = function() {
                this.onerror = null;
                this.src = '/static/default.png';
            };
        }

        if (this.lightboxTitle) this.lightboxTitle.textContent = item.title;
        if (this.lightboxDesc) this.lightboxDesc.textContent = item.description || 'Premium printing project showcasing our quality work.';
        if (this.lightboxCategory) {
            const hasTags = Array.isArray(item.tags) && item.tags.length > 0;
            this.lightboxCategory.textContent = hasTags ? item.tags.join(', ') : '';
            this.lightboxCategory.style.display = hasTags ? 'inline-block' : 'none';
        }

        this.currentIndex = index;
        this.updateNavButtons();

        if (this.lightbox) {
            this.lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        if (this.lightbox) {
            this.lightbox.classList.remove('active');
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
        if (this.prevBtn) this.prevBtn.disabled = this.currentIndex === 0;
        if (this.nextBtn) this.nextBtn.disabled = this.currentIndex === this.galleryItems.length - 1;
    }

    setupEventListeners() {
        if (this.closeLightbox) {
            this.closeLightbox.addEventListener('click', () => this.close());
        }

        if (this.lightbox) {
            this.lightbox.addEventListener('click', (e) => {
                if (e.target === this.lightbox) {
                    this.close();
                }
            });
        }

        if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.goToPrev());
        if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.goToNext());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!this.lightbox || !this.lightbox.classList.contains('active')) return;

            if (e.key === 'Escape') {
                this.close();
            } else if (e.key === 'ArrowLeft') {
                this.goToPrev();
            } else if (e.key === 'ArrowRight') {
                this.goToNext();
            }
        });
    }
}

// Gallery functionality (for gallery.html)
function initGallery() {
    console.log('Initializing gallery');
    // API base URL - adjust if your Django app is served from a different path
    const API_BASE_URL = window.location.origin;
    console.log('API_BASE_URL:', API_BASE_URL);

    // Gallery state
    let currentPage = 1;
    let currentFilters = { search: '', tags: [] };
    let isLoading = false;
    let hasMorePages = true;
    let lastItemObserver;
    let lastObservedItem;

    // DOM elements
    const galleryGrid = document.getElementById('galleryGrid');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const searchInput = document.getElementById('search-input');
    const mobileSearchInput = document.getElementById('mobile-search-input');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noResults = document.getElementById('noResults');

    if (!galleryGrid) return;

    // Initialize lightbox
    const lightbox = new Lightbox();
    lightbox.setupEventListeners();

    // Create skeleton loader
    function createSkeleton() {
        const skeleton = document.createElement('div');
        skeleton.className = 'gallery-item skeleton';
        skeleton.innerHTML = `
            <div class="skeleton-img"></div>
            <div class="skeleton-content">
                <div class="skeleton-line"></div>
                <div class="skeleton-line short"></div>
            </div>
        `;
        return skeleton;
    }

    // Create gallery item
    function createGalleryItem(item) {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item';
        galleryItem.dataset.category = item.tags.join(' ');
        galleryItem.dataset.itemId = item.id; // Store item ID for easy lookup

        const tagsHtml = (item.tags && item.tags.length)
            ? `<span class="category">${item.tags.join(', ')}</span>`
            : '';
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
    }

    // Fetch gallery data from API
    async function fetchGalleryData(page = 1, append = false) {
        if (isLoading) return;

        isLoading = true;
        console.log(`Fetching gallery data: page=${page}, append=${append}, search=${currentFilters.search}, tags=${currentFilters.tags}`);
        if (!append) {
            showLoadingState();
        }

        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: page,
                per_page: GALLERY_PER_PAGE,
                search: currentFilters.search,
                tags: currentFilters.tags
            });

            // Remove empty tags
            if (currentFilters.tags.length === 0) {
                params.delete('tags');
            }

            const url = `${API_BASE_URL}/api/gallery/?${params}`;
            console.log('Fetch URL:', url);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                hasMorePages = data.pagination.has_next;
                currentPage = data.pagination.current_page;
                console.log(`Pagination: current_page=${currentPage}, has_next=${hasMorePages}, total_items=${data.pagination.total_items}`);

                if (append) {
                    // Append new items
                    renderGalleryItems(data.items, true);
                    // Update pagination info after appending
                    updatePaginationInfo(data.pagination);
                } else {
                    // Replace all items
                    lightbox.setItems(data.items);
                    renderGalleryItems(data.items, false);

                    // Update pagination info
                    updatePaginationInfo(data.pagination);
                }
            } else {
                throw new Error(data.message || 'Failed to fetch gallery data');
            }

        } catch (error) {
            console.error('Error fetching gallery data:', error);
            // If API fails, show error message
            if (!append) {
                showError('Failed to load gallery items. Please check your connection and try again.');
            }
        } finally {
            isLoading = false;
            hideLoadingState();
        }
    }

    // Render gallery items
    function renderGalleryItems(items, append = false) {
        if (!append) {
            galleryGrid.innerHTML = '';
        }

        if (items.length === 0) {
            showNoResults();
            return;
        }

        hideNoResults();

        const fragment = document.createDocumentFragment();
        items.forEach(item => {
            const galleryItem = createGalleryItem(item);
            fragment.appendChild(galleryItem);
        });

        galleryGrid.appendChild(fragment);

        // Observe the last item for infinite scroll
        if (lastItemObserver) {
            if (lastObservedItem) {
                lastItemObserver.unobserve(lastObservedItem);
            }
            lastObservedItem = galleryGrid.lastElementChild;
            if (lastObservedItem) {
                lastItemObserver.observe(lastObservedItem);
                console.log('Observing last item:', lastObservedItem);
            }
        }
    }

    // Update pagination info
    function updatePaginationInfo(pagination) {
        console.log('Updating pagination info, has_next:', pagination.has_next);
        // Note: Spinner visibility is handled by show/hide loading state
    }

    // Show loading state
    function showLoadingState() {
        console.log('Showing loading state');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
    }

    // Hide loading state
    function hideLoadingState() {
        console.log('Hiding loading state');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }

    // Show no results message
    function showNoResults() {
        if (noResults) {
            noResults.style.display = 'block';
        }
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }

    // Hide no results message
    function hideNoResults() {
        if (noResults) {
            noResults.style.display = 'none';
        }
    }

    // Show error message
    function showError(message) {
        console.error(message);
        // You could add a toast notification here
    }


    // Filter functionality
    function applyFilters() {
        currentPage = 1;
        fetchGalleryData(1, false);
    }

    // Toggle filter
    function toggleFilter(category) {
        if (category === 'all') {
            currentFilters.tags = [];
        } else {
            const tagIndex = currentFilters.tags.indexOf(category);
            if (tagIndex > -1) {
                currentFilters.tags.splice(tagIndex, 1);
            } else {
                currentFilters.tags.push(category);
            }

            // If no tags selected, show all
            if (currentFilters.tags.length === 0) {
                // Keep 'all' active but don't add it to the tags array
            }
        }

        // Update active buttons
        filterButtons.forEach(btn => {
            if (btn.dataset.filter === 'all') {
                btn.classList.toggle('active', currentFilters.tags.length === 0);
            } else {
                btn.classList.toggle('active', currentFilters.tags.includes(btn.dataset.filter));
            }
        });

        applyFilters();
    }

    // Clear all filters
    function clearFilters() {
        currentFilters.tags = [];
        currentFilters.search = '';

        // Update active buttons
        filterButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === 'all');
        });

        // Clear search inputs
        if (searchInput) searchInput.value = '';
        if (mobileSearchInput) mobileSearchInput.value = '';

        applyFilters();
    }

    // Search functionality with debounce
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function performSearch(query) {
        currentFilters.search = query;
        applyFilters();
    }

    const debouncedSearch = debounce((query) => {
        performSearch(query);
    }, DEBOUNCE_DELAY);


    // Infinite scroll
    function setupInfiniteScroll() {
        console.log('Setting up infinite scroll observer');
        lastItemObserver = new IntersectionObserver((entries) => {
            console.log('Intersection observer triggered on last item:', entries[0].isIntersecting, 'isLoading:', isLoading, 'hasMorePages:', hasMorePages);
            if (entries[0].isIntersecting && !isLoading && hasMorePages) {
                console.log('Loading next page:', currentPage + 1);
                fetchGalleryData(currentPage + 1, true);
            }
        }, {
            rootMargin: INTERSECTION_ROOT_MARGIN,
            threshold: 0.1
        });
        console.log('Infinite scroll observer created');
    }

    // Event listeners
    // Use event delegation for gallery items
    galleryGrid.addEventListener('click', (e) => {
        const galleryItem = e.target.closest('.gallery-item');
        if (galleryItem) {
            // Find the index of the clicked item in gallery items
            const itemId = parseInt(galleryItem.dataset.itemId);
            const index = lightbox.galleryItems.findIndex(i => i.id === itemId);

            if (index !== -1) {
                lightbox.open(index);
            }
        }
    });

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            toggleFilter(button.dataset.filter);
        });
    });

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
            // Update mobile search input to keep them in sync
            if (mobileSearchInput) mobileSearchInput.value = e.target.value;
        });
    }

    if (mobileSearchInput) {
        mobileSearchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
            // Update desktop search input to keep them in sync
            if (searchInput) searchInput.value = e.target.value;
        });
    }


    // Initialize gallery
    fetchGalleryData(1, false);
    setupInfiniteScroll();
}


// Typewriter effect for hero title on index.html
function initTypewriter() {
    try {
        const heading = document.querySelector('.hero-content h1');
        if (!heading) return;

        // Avoid re-initializing
        if (heading.dataset.typed === '1') return;
        heading.dataset.typed = '1';

        const fullText = (heading.textContent || '').trim();
        if (!fullText) return;

        // Prepare for typing
        heading.textContent = '';
        const caret = document.createElement('span');
        caret.className = 'typewriter-caret';
        heading.appendChild(caret);

        let i = 0;
        const TYPE_SPEED = 60; // ms per character
        const START_DELAY = 300; // initial delay for nicer entrance

        function typeNext() {
            if (i < fullText.length) {
                // Insert next character before the caret
                caret.insertAdjacentText('beforebegin', fullText.charAt(i));
                i++;
                setTimeout(typeNext, TYPE_SPEED);
            } else {
                // Optionally keep the caret blinking; do nothing
            }
        }

        setTimeout(typeNext, START_DELAY);
    } catch (e) {
        // Fail silently; this is a progressive enhancement
        console.warn('Typewriter init failed:', e);
    }
}
