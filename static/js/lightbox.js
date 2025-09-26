/**
 * Custom Lightbox Implementation
 * Replaces third-party lightgallery with native functionality
 */

class CustomLightbox {
    constructor(options = {}) {
        this.options = {
            selector: '.gallery-item',
            lightboxId: 'lightbox',
            ...options
        };

        this.currentIndex = 0;
        this.images = [];
        this.isOpen = false;

        this.init();
    }

    init() {
        this.createLightboxHTML();
        this.bindEvents();
        this.setupKeyboardNavigation();
    }

    createLightboxHTML() {
        // Check if lightbox already exists
        if (document.getElementById(this.options.lightboxId)) {
            return;
        }

        const lightboxHTML = `
            <div class="lightbox" id="${this.options.lightboxId}">
                <div class="lightbox-content">
                    <button class="lightbox-close" id="lightboxClose">
                        <i class="fas fa-times"></i>
                    </button>
                    <button class="lightbox-nav lightbox-prev" id="lightboxPrev">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <button class="lightbox-nav lightbox-next" id="lightboxNext">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <img class="lightbox-image" id="lightboxImage" alt="">
                    <div class="lightbox-counter" id="lightboxCounter">1 / 1</div>
                    <div class="lightbox-info">
                        <div class="lightbox-title" id="lightboxTitle"></div>
                        <div class="lightbox-description" id="lightboxDescription"></div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', lightboxHTML);
    }

    bindEvents() {
        const lightbox = document.getElementById(this.options.lightboxId);
        const closeBtn = document.getElementById('lightboxClose');
        const prevBtn = document.getElementById('lightboxPrev');
        const nextBtn = document.getElementById('lightboxNext');

        if (closeBtn) closeBtn.addEventListener('click', () => this.close());
        if (prevBtn) prevBtn.addEventListener('click', () => this.navigate(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => this.navigate(1));

        // Click outside to close
        if (lightbox) {
            lightbox.addEventListener('click', (e) => {
                if (e.target === lightbox) {
                    this.close();
                }
            });
        }

        // Bind gallery items
        this.bindGalleryItems();
    }

    bindGalleryItems() {
        document.querySelectorAll(this.options.selector).forEach((item, index) => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.open(index);
            });
        });
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (!this.isOpen) return;

            switch (e.key) {
                case 'Escape':
                    this.close();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigate(-1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigate(1);
                    break;
            }
        });
    }

    open(index) {
        this.currentIndex = index;
        this.images = this.getImagesData();
        this.isOpen = true;

        if (this.images.length === 0) return;

        this.updateLightboxContent();
        this.updateNavigationButtons();
        this.showLightbox();
    }

    close() {
        this.isOpen = false;
        this.hideLightbox();
    }

    navigate(direction) {
        const newIndex = this.currentIndex + direction;

        if (newIndex >= 0 && newIndex < this.images.length) {
            this.currentIndex = newIndex;
            this.updateLightboxContent();
            this.updateNavigationButtons();
        }
    }


    getImagesData() {
        const items = document.querySelectorAll(this.options.selector);
        return Array.from(items).map((item, index) => ({
            src: item.dataset.src || item.querySelector('img')?.src,
            title: item.querySelector('.gallery-overlay h4, .gallery-overlay .title, .gallery-card-content h3')?.textContent || '',
            description: item.querySelector('.gallery-overlay p, .gallery-card-content p')?.textContent || '',
            alt: item.querySelector('img')?.alt || `Image ${index + 1}`
        }));
    }

    updateLightboxContent() {
        const image = this.images[this.currentIndex];
        if (!image) return;

        const lightboxImage = document.getElementById('lightboxImage');
        const lightboxTitle = document.getElementById('lightboxTitle');
        const lightboxDescription = document.getElementById('lightboxDescription');
        const lightboxCounter = document.getElementById('lightboxCounter');

        // Show loading state immediately
        this.showLoadingState();

        if (lightboxImage) {
            // Set loading state on current image
            lightboxImage.style.opacity = '0.5';
            lightboxImage.style.filter = 'blur(2px)';

            // Create new image for loading
            const img = new Image();

            img.onload = () => {
                // Image loaded, update display
                lightboxImage.src = image.src;
                lightboxImage.alt = image.alt;
                lightboxImage.style.opacity = '1';
                lightboxImage.style.filter = 'blur(0px)';
                this.hideLoadingState();
            };

            img.onerror = () => {
                // Handle error
                console.warn('Image failed to load:', image.src);
                lightboxImage.src = image.src;
                lightboxImage.alt = image.alt || 'Image';
                lightboxImage.style.opacity = '1';
                lightboxImage.style.filter = 'blur(0px)';
                this.hideLoadingState();
            };

            // Start loading the new image
            img.src = image.src;
        }

        // Update text content immediately
        if (lightboxTitle) lightboxTitle.textContent = image.title;
        if (lightboxDescription) lightboxDescription.textContent = image.description;
        if (lightboxCounter) lightboxCounter.textContent = `${this.currentIndex + 1} / ${this.images.length}`;
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('lightboxPrev');
        const nextBtn = document.getElementById('lightboxNext');

        if (prevBtn) prevBtn.style.display = this.currentIndex > 0 ? 'flex' : 'none';
        if (nextBtn) nextBtn.style.display = this.currentIndex < this.images.length - 1 ? 'flex' : 'none';
    }

    showLightbox() {
        const lightbox = document.getElementById(this.options.lightboxId);
        if (lightbox) {
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    hideLightbox() {
        const lightbox = document.getElementById(this.options.lightboxId);
        if (lightbox) {
            lightbox.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    showLoadingState() {
        const lightbox = document.getElementById(this.options.lightboxId);
        if (!lightbox) return;

        let loadingIndicator = document.getElementById('lightboxLoading');
        if (!loadingIndicator) {
            loadingIndicator = document.createElement('div');
            loadingIndicator.id = 'lightboxLoading';
            loadingIndicator.className = 'lightbox-loading';
            loadingIndicator.innerHTML = `
                <div class="loading-content">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Loading...</span>
                </div>
            `;
            lightbox.appendChild(loadingIndicator);
        }

        // Ensure it's visible
        loadingIndicator.style.display = 'flex';
        loadingIndicator.style.zIndex = '10001';
    }

    hideLoadingState() {
        const loadingIndicator = document.getElementById('lightboxLoading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }


    // Public method to refresh gallery items (useful for dynamic content)
    refresh() {
        this.bindGalleryItems();
    }

    // Public method to destroy lightbox
    destroy() {
        const lightbox = document.getElementById(this.options.lightboxId);
        if (lightbox) {
            lightbox.remove();
        }
        document.body.style.overflow = '';
    }
}

// Auto-initialize lightbox when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize lightbox with default settings
    window.lightbox = new CustomLightbox();

    // Also initialize with specific selector if lightgallery element exists
    const lightgalleryElement = document.getElementById('lightgallery');
    if (lightgalleryElement) {
        window.lightboxGallery = new CustomLightbox({
            selector: '.gallery-item'
        });
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CustomLightbox;
}