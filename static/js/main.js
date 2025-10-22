/**
 * Main JavaScript functionality for Peashan Brands website
 * Separated from Django templates for better organization
 */

// Utility functions
const debounce = (fn, delay) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
};

const throttle = (fn, delay) => {
  let lastCall = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      fn(...args);
    }
  };
};

// Navigation functionality
function initNavigation() {
  const nav = document.querySelector("nav");
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  const navHeight = nav.offsetHeight;

  const handleScroll = throttle(() => {
    nav.classList.toggle("scrolled", window.scrollY > 100);
  }, 100);

  const handleResize = throttle(() => {
    if (window.innerWidth > 768) {
      mobileMenu.style.display = "none";
      mobileMenuBtn.setAttribute("data-icon", "hamburger");
    }
  }, 100);

  window.addEventListener("scroll", handleScroll, { passive: true });
  window.addEventListener("resize", handleResize, { passive: true });

  mobileMenuBtn.addEventListener("click", () => {
    const isVisible = mobileMenu.style.display === "block";
    mobileMenu.style.display = isVisible ? "none" : "block";
    mobileMenuBtn.setAttribute("data-icon", isVisible ? "hamburger" : "close");
  });

  document.addEventListener("click", (e) => {
    const link = e.target.closest(".nav-link, .mobile-menu-link");
    if (!link) return;

    e.preventDefault();
    const targetId = link.getAttribute("href");
    const targetSection = document.querySelector(targetId);

    if (!targetSection) return;

    window.scrollTo({
      top: targetSection.offsetTop - navHeight,
      behavior: "smooth",
    });

    if (mobileMenu.style.display === "block") {
      mobileMenu.style.display = "none";
      mobileMenuBtn.setAttribute("data-icon", "hamburger");
    }
  });
}

// Scroll effects and animations
function initScrollEffects() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -100px 0px",
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.remove("animate-out");
        entry.target.classList.add("animate-in");
      }
    });
  }, observerOptions);

  const animatedElements = document.querySelectorAll(
    ".service-card, .portfolio-item, .contact-card"
  );
  animatedElements.forEach((el, index) => {
    el.classList.add("animate-out");
    el.style.setProperty("--transition-delay", `${index * 0.1}s`);
    observer.observe(el);
  });

  const portfolioObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          const item = entry.target;
          item.style.animationDelay = `${index * 1}s`;
          item.classList.add("animate-in");
        }
      });
    },
    { threshold: 0.1 }
  );

  const portfolioItems = document.querySelectorAll(".portfolio-item");
  portfolioItems.forEach((item, index) => {
    portfolioObserver.observe(item);
  });

  const bgElement1 = document.getElementById("bg-element-1");
  if (!bgElement1) return;

  let mouseX = 0,
    mouseY = 0,
    currentX = 0,
    currentY = 0;

  const handleMouseMove = throttle((e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 50;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 50;
  }, 16);

  document.addEventListener("mousemove", handleMouseMove, {
    passive: true,
  });

  function animateBackground() {
    currentX += (mouseX - currentX) * 0.05;
    currentY += (mouseY - currentY) * 0.05;
    bgElement1.style.transform = `translate(${currentX}px, ${currentY}px)`;
    requestAnimationFrame(animateBackground);
  }

  animateBackground();
}

// Portfolio functionality
function initPortfolio() {
  const portfolioGrid = document.querySelector(".portfolio-grid");
  const portfolioItems = document.querySelectorAll(".portfolio-item");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const searchInput = document.getElementById("portfolio-search");
  const searchClear = document.getElementById("search-clear");
  const lightbox = document.getElementById("lightbox");
  const lightboxImage = document.getElementById("lightbox-image");
  const lightboxTitle = document.getElementById("lightbox-title");
  const lightboxDescription = document.getElementById("lightbox-description");
  const closeLightbox = document.getElementById("close-lightbox");
  const seeMoreBtn = document.getElementById("see-more-portfolio");
  const emptyState = document.getElementById("empty-portfolio-state");
  const noResultsState = document.getElementById("no-results-state");

  let currentPage = 1;
  let currentFilters = [];
  let currentSearch = "";
  let isLoading = false;
  let hasMorePages = true;
  const itemsPerPage = 6;

  // Load initial portfolio items on page load
  loadPortfolioItems(1, false);

  function applyFilters() {
    currentPage = 1;
    loadPortfolioItems(1, false);
  }

  // Function to load portfolio items from server
  async function loadPortfolioItems(page = 1, append = false) {
    if (isLoading) return;

    isLoading = true;
    if (!append) {
      showLoadingState();
    }

    try {
      const params = new URLSearchParams({
        page: page,
        per_page: itemsPerPage,
        search: currentSearch,
      });

      if (currentFilters.length > 0) {
        params.set("tags", currentFilters.join(","));
      }

      const response = await fetch(`/api/gallery/?${params}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();

      if (data.success) {
        hasMorePages = data.pagination.has_next;
        currentPage = data.pagination.current_page;

        if (append) {
          renderPortfolioItems(data.items, true);
        } else {
          renderPortfolioItems(data.items, false);
        }

        // Update button visibility
        if (seeMoreBtn) {
          seeMoreBtn.style.display = hasMorePages ? "inline-flex" : "none";
        }
      } else {
        throw new Error(data.message || "Failed to fetch portfolio data");
      }
    } catch (error) {
      console.error("Error loading portfolio items:", error);
      showNotification(
        "Failed to load portfolio items. Please try again.",
        "error"
      );
    } finally {
      isLoading = false;
      hideLoadingState();
    }
  }

  function showLoadingState() {
    const loadingElement = document.getElementById("portfolioLoading");
    if (loadingElement) {
      loadingElement.style.display = "flex";
    }
  }

  function hideLoadingState() {
    const loadingElement = document.getElementById("portfolioLoading");
    if (loadingElement) {
      loadingElement.style.display = "none";
    }
  }

  function renderPortfolioItems(items, append = false) {
    const portfolioGrid = document.getElementById("portfolioGrid");
    if (!portfolioGrid) return;

    if (!append) {
      portfolioGrid.innerHTML = "";
    }

    if (items.length === 0) {
      showNoResults();
      return;
    }

    hideNoResults();

    const fragment = document.createDocumentFragment();
    items.forEach((item, index) => {
      const portfolioItem = createPortfolioItemElement(item, index);
      fragment.appendChild(portfolioItem);
    });

    portfolioGrid.appendChild(fragment);
  }

  function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replaceAll("&", "&")
      .replaceAll("<", "<")
      .replaceAll(">", ">")
      .replaceAll('"', "")
      .replaceAll("'", "'");
  }

  function truncateString(str, maxLen) {
    if (str == null) return "";
    if (str.length <= maxLen) return str;
    // keep the total length <= maxLen, using a single ellipsis character
    return str.slice(0, maxLen - 1) + "…";
  }

  function createPortfolioItemElement(item, index) {
    const div = document.createElement("div");
    div.className = "portfolio-item fade-in-up";
    div.dataset.category = (item.tags || []).join(" ");
    div.dataset.itemId = item.id ?? "";
    div.style.setProperty("--animation-delay", `${index * 0.1}s`);

    const tagsHtml =
      item.tags && item.tags.length
        ? item.tags
            .map(
              (tag) => `<span class="portfolio-tag">${escapeHtml(tag)}</span>`
            )
            .join("")
        : "";

    const rawDescription =
      item.description && item.description.trim()
        ? item.description
        : "Premium printing project showcasing our quality work.";
    const truncated = truncateString(rawDescription, 120);
    const safeDescription = escapeHtml(truncated);
    const safeFullDescription = escapeHtml(rawDescription);

    div.dataset.fullDescription = safeFullDescription;

    div.innerHTML = `
    <div class="portfolio-image-wrapper">
      <img src="${escapeHtml(
        item.thumbnail || "/static/default.jpg"
      )}" alt="${escapeHtml(item.title || "")}" class="portfolio-image"
           onerror="this.onerror=null; this.src='/static/default.jpg';">
      <div class="portfolio-overlay">
        <div class="portfolio-overlay-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"></path>
          </svg>
        </div>
      </div>
    </div>

    <div class="portfolio-content">
      <h3 class="portfolio-title">${escapeHtml(item.title || "")}</h3>
      <p class="portfolio-description">${safeDescription}</p>
      ${tagsHtml ? `<div class="portfolio-tags">${tagsHtml}</div>` : ""}
      <div class="portfolio-link text-gradient">
        <span>View Details</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"></path>
        </svg>
      </div>
    </div>
  `;

    return div;
  }

  function showNoResults() {
    const portfolioGrid = document.getElementById("portfolioGrid");
    const portfolioControls = document.getElementById("portfolio-controls");
    const portfolioFilters = document.getElementById("portfolio-filters");
    const noResultsState = document.getElementById("no-results-state");

    if (portfolioGrid) {
      portfolioGrid.style.display = "none";
    }

    if (portfolioControls) {
      portfolioControls.style.display = "none";
    }

    if (portfolioFilters) {
      portfolioFilters.style.display = "none";
    }

    if (noResultsState) {
      noResultsState.style.display = "flex";
    }

    if (seeMoreBtn) seeMoreBtn.style.display = "none";
  }

  function hideNoResults() {
    const portfolioGrid = document.getElementById("portfolioGrid");
    const portfolioControls = document.getElementById("portfolio-controls");
    const portfolioFilters = document.getElementById("portfolio-filters");
    const noResultsState = document.getElementById("no-results-state");

    if (portfolioGrid) {
      portfolioGrid.style.display = "grid";
    }

    if (portfolioControls) {
      portfolioControls.style.display = "flex";
    }

    // Filters are now conditionally rendered in template, so just show them
    if (portfolioFilters) {
      portfolioFilters.style.display = "flex";
    }

    if (noResultsState) {
      noResultsState.style.display = "none";
    }
  }

  portfolioGrid?.addEventListener("click", (e) => {
    const filterBtn = e.target.closest(".filter-btn");
    if (filterBtn) {
      const filterValue = filterBtn.dataset.filter;
      if (filterValue === "all") {
        // Clear all filters when "All" is clicked
        filterBtns.forEach((b) => b.classList.remove("active"));
        filterBtn.classList.add("active");
        currentFilters = [];
      } else {
        // Toggle individual tag filters
        const allBtn = document.querySelector('.filter-btn[data-filter="all"]');
        allBtn?.classList.remove("active");

        if (currentFilters.includes(filterValue)) {
          // Remove filter
          currentFilters = currentFilters.filter((f) => f !== filterValue);
          filterBtn.classList.remove("active");
          // If no filters selected, activate "All"
          if (currentFilters.length === 0) {
            allBtn?.classList.add("active");
          }
        } else {
          // Add filter
          currentFilters.push(filterValue);
          filterBtn.classList.add("active");
        }
      }
      applyFilters();
      return;
    }

    const portfolioItem = e.target.closest(".portfolio-item");
    if (portfolioItem && !portfolioItem.classList.contains("hidden")) {
      const img = portfolioItem.querySelector(".portfolio-image");
      const title = portfolioItem.querySelector(".portfolio-title").textContent;
      const description = portfolioItem.dataset.fullDescription;

      lightboxImage.src = img.src;
      lightboxImage.alt = title;
      lightboxTitle.textContent = title;
      lightboxDescription.textContent = description;
      lightbox.style.display = "flex";
      document.body.style.overflow = "hidden";
    }
  });

  const handleSearch = debounce((e) => {
    currentSearch = e.target.value.trim();
    searchClear.style.display = currentSearch ? "flex" : "none";
    applyFilters();
  }, 300);

  searchInput?.addEventListener("input", handleSearch);

  searchClear?.addEventListener("click", () => {
    searchInput.value = "";
    currentSearch = "";
    searchClear.style.display = "none";
    applyFilters();
  });

  // Clear search and filters button
  const clearSearchFiltersBtn = document.getElementById("clear-search-filters");
  clearSearchFiltersBtn?.addEventListener("click", () => {
    // Clear search
    searchInput.value = "";
    currentSearch = "";
    searchClear.style.display = "none";

    // Clear all filters
    currentFilters = [];
    filterBtns.forEach((btn) => btn.classList.remove("active"));
    const allBtn = document.querySelector('.filter-btn[data-filter="all"]');
    allBtn?.classList.add("active");

    applyFilters();
  });

  // Initialize "All" filter as active
  const allFilterBtn = document.querySelector('.filter-btn[data-filter="all"]');
  if (allFilterBtn) {
    allFilterBtn.classList.add("active");
  }

  seeMoreBtn?.addEventListener("click", () => {
    const seeMoreText = document.getElementById("see-more-text");
    const seeMoreLoading = document.getElementById("see-more-loading");

    if (seeMoreText) seeMoreText.style.display = "none";
    if (seeMoreLoading) seeMoreLoading.style.display = "block";

    currentPage += 1;
    loadPortfolioItems(currentPage, true).finally(() => {
      if (seeMoreText) seeMoreText.style.display = "inline";
      if (seeMoreLoading) seeMoreLoading.style.display = "none";
    });
  });

  // Lightbox zoom functionality
  let currentZoom = 1;
  let isDragging = false;
  let startX, startY, initialX, initialY;
  let currentTranslateX = 0;
  let currentTranslateY = 0;

  const zoomInBtn = document.getElementById("zoom-in-btn");
  const zoomOutBtn = document.getElementById("zoom-out-btn");
  const zoomResetBtn = document.getElementById("zoom-reset-btn");

  const minZoom = 1;
  const maxZoom = 3;
  const zoomStep = 0.25;

  function updateImageTransform() {
    lightboxImage.style.transform = `scale(${currentZoom}) translate(${currentTranslateX}px, ${currentTranslateY}px)`;
    lightboxImage.classList.toggle("zoomed", currentZoom > 1);
  }

  function zoomIn() {
    if (currentZoom < maxZoom) {
      currentZoom = Math.min(currentZoom + zoomStep, maxZoom);
      updateImageTransform();
    }
  }

  function zoomOut() {
    if (currentZoom > minZoom) {
      currentZoom = Math.max(currentZoom - zoomStep, minZoom);
      if (currentZoom === minZoom) {
        currentTranslateX = 0;
        currentTranslateY = 0;
      }
      updateImageTransform();
    }
  }

  function resetZoom() {
    currentZoom = minZoom;
    currentTranslateX = 0;
    currentTranslateY = 0;
    updateImageTransform();
  }

  function handleWheel(e) {
    e.preventDefault();
    if (e.deltaY < 0) {
      zoomIn();
    } else {
      zoomOut();
    }
  }

  function handleMouseDown(e) {
    if (currentZoom > 1) {
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      initialX = currentTranslateX;
      initialY = currentTranslateY;
      lightboxImage.style.cursor = "grabbing";
    }
  }

  function handleMouseMove(e) {
    if (isDragging && currentZoom > 1) {
      const deltaX = e.clientX - startX;
      const deltaY = e.clientY - startY;
      currentTranslateX = initialX + deltaX / currentZoom;
      currentTranslateY = initialY + deltaY / currentZoom;
      updateImageTransform();
    }
  }

  function handleMouseUp() {
    isDragging = false;
    lightboxImage.style.cursor = currentZoom > 1 ? "grab" : "default";
  }

  zoomInBtn?.addEventListener("click", zoomIn);
  zoomOutBtn?.addEventListener("click", zoomOut);
  zoomResetBtn?.addEventListener("click", resetZoom);

  lightboxImage?.addEventListener("wheel", handleWheel, { passive: false });
  lightboxImage?.addEventListener("mousedown", handleMouseDown);
  document.addEventListener("mousemove", handleMouseMove);
  document.addEventListener("mouseup", handleMouseUp);

  const closeLightboxHandler = () => {
    lightbox.style.display = "none";
    document.body.style.overflow = "auto";
    resetZoom();
  };

  closeLightbox?.addEventListener("click", closeLightboxHandler);

  lightbox?.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightboxHandler();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && lightbox.style.display === "flex") {
      closeLightboxHandler();
    }
    if (lightbox.style.display === "flex") {
      if (e.key === "+" || e.key === "=") {
        e.preventDefault();
        zoomIn();
      } else if (e.key === "-") {
        e.preventDefault();
        zoomOut();
      } else if (e.key === "0") {
        e.preventDefault();
        resetZoom();
      }
    }
  });
}

// Partners carousel functionality
function initPartners() {
  const partnerItems = document.querySelectorAll(".partner-item");
  const dots = document.querySelectorAll(".partners-dots .dot");
  const itemCount = partnerItems.length;

  if (itemCount === 0) return;

  let currentIndex = 0;
  let autoAdvanceInterval;

  function getResponsivePositions() {
    const isMobile = window.innerWidth <= 480;
    const isTablet = window.innerWidth <= 768 && window.innerWidth > 480;

    if (isMobile) {
      return [
        { translateX: 0, scale: 1.1, opacity: 1, zIndex: 7 },
        { translateX: 75, scale: 0.9, opacity: 0.6, zIndex: 6 },
        { translateX: -75, scale: 0.9, opacity: 0.6, zIndex: 6 },
        { translateX: 150, scale: 0.6, opacity: 0.3, zIndex: 5 },
        { translateX: -150, scale: 0.6, opacity: 0.3, zIndex: 5 },
        { translateX: 225, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: -225, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: 0, scale: 0.2, opacity: 0, zIndex: 1 }, // Hidden
        { translateX: 0, scale: 0.1, opacity: 0, zIndex: 1 }, // Hidden
      ];
    } else if (isTablet) {
      return [
        { translateX: 0, scale: 1.2, opacity: 1, zIndex: 7 },
        { translateX: 150, scale: 1.0, opacity: 0.7, zIndex: 6 },
        { translateX: -150, scale: 1.0, opacity: 0.7, zIndex: 6 },
        { translateX: 300, scale: 0.7, opacity: 0.4, zIndex: 5 },
        { translateX: -300, scale: 0.7, opacity: 0.4, zIndex: 5 },
        { translateX: 450, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: -450, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: 0, scale: 0.2, opacity: 0, zIndex: 1 }, // Hidden
        { translateX: 0, scale: 0.1, opacity: 0, zIndex: 1 }, // Hidden
      ];
    } else {
      return [
        { translateX: 0, scale: 1.3, opacity: 1, zIndex: 7 },
        { translateX: 220, scale: 1.0, opacity: 0.7, zIndex: 6 },
        { translateX: -220, scale: 1.0, opacity: 0.7, zIndex: 6 },
        { translateX: 440, scale: 0.7, opacity: 0.4, zIndex: 5 },
        { translateX: -440, scale: 0.7, opacity: 0.4, zIndex: 5 },
        { translateX: 660, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: -660, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: 880, scale: 0.2, opacity: 0.05, zIndex: 3 },
        { translateX: -880, scale: 0.2, opacity: 0.05, zIndex: 3 },
      ];
    }
  }

  function getPosition(relativeIndex) {
    const currentPositions = getResponsivePositions();
    if (relativeIndex === 0) return currentPositions[0];
    if (relativeIndex === 1 || relativeIndex === itemCount - 1) {
      return relativeIndex === 1 ? currentPositions[1] : currentPositions[2];
    }
    if (relativeIndex === 2 || relativeIndex === itemCount - 2) {
      return relativeIndex === 2 ? currentPositions[3] : currentPositions[4];
    }
    if (relativeIndex === 3 || relativeIndex === itemCount - 3) {
      return relativeIndex === 3 ? currentPositions[5] : currentPositions[6];
    }
    return relativeIndex < itemCount / 2
      ? currentPositions[7]
      : currentPositions[8];
  }

  function updateCarousel(animate = true) {
    requestAnimationFrame(() => {
      partnerItems.forEach((item, index) => {
        const relativeIndex = (index - currentIndex + itemCount) % itemCount;
        const pos = getPosition(relativeIndex);

        item.classList.toggle("partner-animate", animate);
        item.style.transform = `translateX(${pos.translateX}px) scale(${pos.scale})`;
        item.style.opacity = pos.opacity;
        item.style.zIndex = pos.zIndex;
      });

      dots.forEach((dot, index) => {
        dot.classList.toggle("active", index === currentIndex);
      });
    });
  }

  function startAutoAdvance() {
    stopAutoAdvance();
    autoAdvanceInterval = setInterval(() => {
      currentIndex = (currentIndex + 1) % itemCount;
      updateCarousel();
    }, 4000);
  }

  function stopAutoAdvance() {
    if (autoAdvanceInterval) {
      clearInterval(autoAdvanceInterval);
      autoAdvanceInterval = null;
    }
  }

  document.addEventListener("click", (e) => {
    const dot = e.target.closest(".partners-dots .dot");
    if (dot) {
      currentIndex = Array.from(dots).indexOf(dot);
      updateCarousel();
      startAutoAdvance();
      return;
    }

    const partner = e.target.closest(".partner-item");
    if (partner) {
      const index = Array.from(partnerItems).indexOf(partner);
      currentIndex = index;
      updateCarousel();
      startAutoAdvance();
    }
  });

  updateCarousel(false);
  startAutoAdvance();

  // Update carousel on window resize
  window.addEventListener(
    "resize",
    throttle(() => {
      updateCarousel(false);
    }, 100)
  );
}

// Form and interaction functionality
function initForms() {
  const contactForm = document.querySelector(".contact-form");
  const viewWorkBtn = document.getElementById("view-work-btn");
  const getQuoteBtn = document.getElementById("get-quote-btn");
  const nav = document.querySelector("nav");
  const navHeight = nav?.offsetHeight || 0;

  const scrollToSection = (selector) => {
    const section = document.querySelector(selector);
    if (!section) return;

    window.scrollTo({
      top: section.offsetTop - navHeight,
      behavior: "smooth",
    });
  };

  viewWorkBtn?.addEventListener("click", () => scrollToSection("#portfolio"));
  getQuoteBtn?.addEventListener("click", () => scrollToSection("#contact"));

  contactForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(contactForm);
    const submitBtn = contactForm.querySelector('[type="submit"]');
    const originalBtnHTML = submitBtn ? submitBtn.innerHTML : "";

    // Helper to toggle a nicer loading state on the button
    function setButtonLoading(btn, loading, text = "Sending...") {
      if (!btn) return;
      if (loading) {
        if (!btn.dataset._origHtml) btn.dataset._origHtml = btn.innerHTML;
        btn.classList.add("btn-loading");
        btn.setAttribute("aria-busy", "true");
        btn.disabled = true;
        btn.innerHTML = `
          <span class="btn-spinner" aria-hidden="true" style="display:inline-block;margin-right:8px;vertical-align:middle">
            <svg width="18" height="18" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
              <g transform="translate(25,25)">
                <g>
                  <circle cx="0" cy="0" r="20" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-dasharray="31.4 31.4"/>
                  <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0" to="360" dur="1s" repeatCount="indefinite"/>
                </g>
              </g>
            </svg>
          </span>
          <span>${text}</span>
        `;
      } else {
        btn.classList.remove("btn-loading");
        btn.removeAttribute("aria-busy");
        btn.disabled = false;
        btn.innerHTML =
          btn.dataset._origHtml || originalBtnHTML || btn.innerHTML;
        try {
          delete btn.dataset._origHtml;
        } catch (err) {}
      }
    }

    // Require name and message; require either email OR phone (not both)
    const requiredFields = ["name", "message"];
    const missingFields = requiredFields.filter(
      (field) => !formData.get(field)?.toString().trim()
    );

    if (missingFields.length > 0) {
      showNotification("Please fill in your name and message", "error");
      return;
    }

    // Ensure either email or phone is provided
    const email = (formData.get("email") || "").toString().trim();
    const phone = (formData.get("phone") || "").toString().trim();

    if (!email && !phone) {
      showNotification(
        "Please provide either an email address or a phone number",
        "error"
      );
      return;
    }

    // If service wasn't selected, default to 'other'
    if (!(formData.get("service") || "").toString().trim()) {
      formData.set("service", "other");
    }

    // Validate email only if provided
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showNotification("Please enter a valid email address", "error");
      return;
    }

    // Prepare fetch - show nicer loading state
    setButtonLoading(submitBtn, true, "Sending...");

    try {
      const action = contactForm.getAttribute("action") || "/contact/";
      // Grab CSRF token from the form (rendered by Django) or cookie fallback
      const csrftoken = (
        document.querySelector("[name=csrfmiddlewaretoken]") || {}
      ).value;

      const resp = await fetch(action, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken || "",
        },
        body: formData,
      });

      const data = await resp.json().catch(() => ({}));

      if (resp.ok && data.success !== false) {
        showNotification(
          data.message
            ? data.message
            : "Thank you! We'll get back to you shortly.",
          "success"
        );
        contactForm.reset();
      } else {
        showNotification(
          data.message
            ? data.message
            : "Failed to submit form. Please try again later.",
          "error"
        );
      }
    } catch (err) {
      console.error("Contact form submit error", err);
      showNotification(
        "There was an error submitting the form. Please try again later.",
        "error"
      );
    } finally {
      setButtonLoading(submitBtn, false);
    }
  });
}

// WhatsApp functionality
function initWhatsApp() {
  const whatsappFloat = document.getElementById("whatsapp-float");
  const whatsappModal = document.getElementById("whatsapp-modal");
  const whatsappModalClose = document.getElementById("whatsapp-modal-close");
  const whatsappForm = document.getElementById("whatsapp-form");

  whatsappFloat?.addEventListener("click", () => {
    if (!window.config || !window.config.contact_number) return; // Don't open modal if no contact number
    const isVisible = whatsappModal.style.display === "block";
    whatsappModal.style.display = isVisible ? "none" : "block";
  });

  whatsappModalClose?.addEventListener("click", () => {
    whatsappModal.style.display = "none";
  });

  whatsappForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const messageField = document.getElementById("whatsapp-message");
    const message = messageField?.value.trim();

    if (!message) {
      showNotification("Please enter a message", "error");
      return;
    }

    const phoneNumber = window.config.contact_number.replace(/\D/g, "");
    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(
      message
    )}`;

    window.open(whatsappUrl, "_blank");
    whatsappModal.style.display = "none";
    whatsappForm.reset();
  });

  document.addEventListener("click", (e) => {
    if (
      !whatsappFloat?.contains(e.target) &&
      !whatsappModal?.contains(e.target)
    ) {
      whatsappModal.style.display = "none";
    }
  });
}

// Animation effects
function initAnimations() {
  const serviceCards = document.querySelectorAll(".service-card");

  serviceCards.forEach((card) => {
    const icon = card.querySelector(".service-icon");

    card.addEventListener("mouseenter", () => {
      if (icon) {
        icon.classList.add("bounce-animation");
      }
    });

    card.addEventListener("mouseleave", () => {
      if (icon) {
        icon.classList.remove("bounce-animation");
      }
    });
  });
}

// Notification system
function showNotification(message, type = "info") {
  const existing = document.querySelector(".notification");
  existing?.remove();

  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => notification.remove(), 3000);
}

// Initialize all functionality when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initScrollEffects();
  initPortfolio();
  initPartners();
  initForms();
  initWhatsApp();
  initAnimations();
});
