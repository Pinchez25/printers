/**
 * Portfolio functionality module
 */
import { debounce, escapeHtml, truncateString } from "./utils.js";
import {
  show,
  hide,
  toggle,
  delegateEvent,
  createFragment,
} from "./dom-utils.js";
import { showNotification } from "./notifications.js";
import { CONFIG } from "../config.js";

/**
 * Portfolio state management
 */
class PortfolioState {
  constructor() {
    this.currentPage = 1;
    this.filters = [];
    this.searchQuery = "";
    this.isLoading = false;
    this.hasMorePages = true;
  }

  reset() {
    this.currentPage = 1;
    this.filters = [];
    this.searchQuery = "";
  }

  update(changes) {
    Object.assign(this, changes);
  }
}

/**
 * Initialise portfolio functionality
 */
export function initPortfolio() {
  const elements = cachePortfolioElements();
  if (!elements.grid) return;

  const state = new PortfolioState();

  // Load initial portfolio items
  loadPortfolioItems(elements, state, 1, false);

  // Setup event listeners
  setupPortfolioEvents(elements, state);
  setupLightboxEvents(elements);
}

/**
 * Shared Zoomist instance for lightbox
 */
let sharedZoomist = null;

/**
 * Cache all portfolio DOM elements
 */
function cachePortfolioElements() {
  return {
    grid: document.getElementById("portfolioGrid"),
    loading: document.getElementById("portfolioLoading"),
    noResults: document.getElementById("no-results-state"),
    controls: document.getElementById("portfolio-controls"),
    filters: document.getElementById("portfolio-filters"),
    filterBtns: document.querySelectorAll(".filter-btn"),
    searchInput: document.getElementById("portfolio-search"),
    searchClear: document.getElementById("search-clear"),
    clearFiltersBtn: document.getElementById("clear-search-filters"),
    seeMoreBtn: document.getElementById("see-more-portfolio"),
    seeMoreText: document.getElementById("see-more-text"),
    seeMoreLoading: document.getElementById("see-more-loading"),
    lightbox: document.getElementById("lightbox"),
    lightboxImage: document.getElementById("lightbox-image"),
    lightboxTitle: document.getElementById("lightbox-title"),
    lightboxDescription: document.getElementById("lightbox-description"),
    closeLightbox: document.getElementById("close-lightbox"),
    zoomistContainer: document.querySelector(".zoomist-container"),
    template: document.getElementById("portfolio-item-template"),
  };
}

/**
 * Setup portfolio event listeners
 */
function setupPortfolioEvents(elements, state) {
  // Filter buttons
  delegateEvent(
    elements.grid?.parentElement,
    ".filter-btn",
    "click",
    (e, btn) => {
      handleFilterClick(btn, elements, state);
    }
  );

  // Portfolio item clicks
  delegateEvent(elements.grid, ".portfolio-item", "click", (e, item) => {
    if (!item.classList.contains("hidden")) {
      openLightbox(item, elements);
    }
  });

  // Search input
  if (elements.searchInput) {
    const handleSearch = debounce((e) => {
      state.searchQuery = e.target.value.trim();
      toggle(elements.searchClear, state.searchQuery, "flex");
      applyFilters(elements, state);
    }, CONFIG.ANIMATION.SEARCH_DEBOUNCE);

    elements.searchInput.addEventListener("input", handleSearch);
  }

  // Search clear button
  elements.searchClear?.addEventListener("click", () => {
    if (elements.searchInput) {
      elements.searchInput.value = "";
      state.searchQuery = "";
      hide(elements.searchClear);
      applyFilters(elements, state);
    }
  });

  // Clear all filters button
  elements.clearFiltersBtn?.addEventListener("click", () => {
    clearAllFilters(elements, state);
  });

  // See more button
  elements.seeMoreBtn?.addEventListener("click", () => {
    handleSeeMore(elements, state);
  });

  // Initialise "All" filter as active
  const allFilterBtn = document.querySelector('.filter-btn[data-filter="all"]');
  if (allFilterBtn) {
    allFilterBtn.classList.add("active");
  }
}

/**
 * Handle filter button click
 */
function handleFilterClick(btn, elements, state) {
  const filterValue = btn.dataset.filter;

  if (filterValue === "all") {
    // Clear all filters
    elements.filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.filters = [];
  } else {
    // Toggle individual filter
    const allBtn = document.querySelector('.filter-btn[data-filter="all"]');
    allBtn?.classList.remove("active");

    if (state.filters.includes(filterValue)) {
      // Remove filter
      state.filters = state.filters.filter((f) => f !== filterValue);
      btn.classList.remove("active");

      // If no filters, activate "All"
      if (state.filters.length === 0) {
        allBtn?.classList.add("active");
      }
    } else {
      // Add filter
      state.filters.push(filterValue);
      btn.classList.add("active");
    }
  }

  applyFilters(elements, state);
}

/**
 * Apply current filters and search
 */
function applyFilters(elements, state) {
  state.currentPage = 1;
  loadPortfolioItems(elements, state, 1, false);
}

/**
 * Clear all filters and search
 */
function clearAllFilters(elements, state) {
  if (elements.searchInput) {
    elements.searchInput.value = "";
  }
  state.searchQuery = "";
  hide(elements.searchClear);

  state.filters = [];
  elements.filterBtns.forEach((btn) => btn.classList.remove("active"));

  const allBtn = document.querySelector('.filter-btn[data-filter="all"]');
  allBtn?.classList.add("active");

  applyFilters(elements, state);
}

/**
 * Handle see more button click
 */
function handleSeeMore(elements, state) {
  hide(elements.seeMoreText);
  show(elements.seeMoreLoading, "block");

  state.currentPage += 1;
  loadPortfolioItems(elements, state, state.currentPage, true).finally(() => {
    show(elements.seeMoreText, "inline");
    hide(elements.seeMoreLoading);
  });
}

/**
 * Load portfolio items from server
 */
async function loadPortfolioItems(elements, state, page = 1, append = false) {
  if (state.isLoading) return;

  state.isLoading = true;
  if (!append) {
    show(elements.loading, "flex");
  }

  try {
    const params = new URLSearchParams({
      page: page,
      per_page: CONFIG.PORTFOLIO.ITEMS_PER_PAGE,
      search: state.searchQuery,
    });

    if (state.filters.length > 0) {
      params.set("tags", state.filters.join(","));
    }

    const response = await fetch(`${CONFIG.PORTFOLIO.API_ENDPOINT}?${params}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      state.hasMorePages = data.pagination.has_next;
      state.currentPage = data.pagination.current_page;

      renderPortfolioItems(elements, data.items, append);

      // Update see more button visibility
      toggle(elements.seeMoreBtn, state.hasMorePages, "inline-flex");
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
    state.isLoading = false;
    hide(elements.loading);
  }
}

/**
 * Render portfolio items to the grid
 */
function renderPortfolioItems(elements, items, append = false) {
  if (!append) {
    elements.grid.innerHTML = "";
  }

  if (items.length === 0) {
    showNoResults(elements);
    return;
  }

  hideNoResults(elements);

  const portfolioElements = items.map((item, index) =>
    createPortfolioItemElement(elements.template, item, index)
  );

  const fragment = createFragment(portfolioElements);
  elements.grid.appendChild(fragment);
}

/**
 * Create portfolio item element from template
 */
function createPortfolioItemElement(template, item, index) {
  if (!template) {
    console.error("Portfolio template not found");
    return document.createElement("div");
  }

  const clone = template.content.cloneNode(true);
  const div = clone.querySelector(".portfolio-item");

  // Set data attributes
  div.dataset.category = (item.tags || []).join(" ");
  div.dataset.itemId = item.id ?? "";
  div.dataset.fullDescription = escapeHtml(
    item.description || CONFIG.PORTFOLIO.DEFAULT_DESCRIPTION
  );
  div.style.setProperty("--animation-delay", `${index * 0.1}s`);

  // Set image with loading state
  const img = clone.querySelector(".portfolio-image");
  const imgWrapper = clone.querySelector(".portfolio-image-wrapper");
  
  // Add loading class to wrapper
  imgWrapper.classList.add("loading");
  
  img.alt = item.title || "";
  
  // Handle image load
  img.onload = function () {
    this.classList.add("loaded");
    imgWrapper.classList.remove("loading");
  };
  
  img.onerror = function () {
    this.onerror = null;
    this.src = CONFIG.PORTFOLIO.DEFAULT_IMAGE;
    this.classList.add("loaded");
    imgWrapper.classList.remove("loading");
  };
  
  // Set src after handlers are attached
  img.src = item.thumbnail || CONFIG.PORTFOLIO.DEFAULT_IMAGE;

  // Set title and description
  clone.querySelector(".portfolio-title").textContent = item.title || "";

  const description =
    item.description?.trim() || CONFIG.PORTFOLIO.DEFAULT_DESCRIPTION;
  const truncated = truncateString(
    description,
    CONFIG.PORTFOLIO.DESCRIPTION_MAX_LENGTH
  );
  clone.querySelector(".portfolio-description").textContent = truncated;

  // Handle tags
  const tagsContainer = clone.querySelector(".portfolio-tags");
  if (item.tags?.length) {
    item.tags.forEach((tag) => {
      const span = document.createElement("span");
      span.className = "portfolio-tag";
      span.textContent = tag;
      tagsContainer.appendChild(span);
    });
  } else {
    tagsContainer.remove();
  }

  return clone;
}

/**
 * Show no results state
 */
function showNoResults(elements) {
  hide(elements.grid);
  hide(elements.controls);
  hide(elements.filters);
  show(elements.noResults, "flex");
  hide(elements.seeMoreBtn);
}

/**
 * Hide no results state
 */
function hideNoResults(elements) {
  show(elements.grid, "grid");
  show(elements.controls, "flex");
  show(elements.filters, "flex");
  hide(elements.noResults);
}

/**
 * Open lightbox with portfolio item
 */
function openLightbox(item, elements) {
  const img = item.querySelector(".portfolio-image");
  const title = item.querySelector(".portfolio-title").textContent;
  const description = item.dataset.fullDescription;
  const imageWrapper = elements.lightboxImage.parentElement;

  // Reset image state
  elements.lightboxImage.classList.remove("loaded");
  imageWrapper.classList.add("loading");

  // Set text content
  elements.lightboxTitle.textContent = title;
  elements.lightboxDescription.textContent = description;
  elements.lightboxImage.alt = title;

  // Handle image load
  elements.lightboxImage.onload = function () {
    this.classList.add("loaded");
    imageWrapper.classList.remove("loading");
    // Initialise Zoomist after image loads
    initialiseZoomist(elements);
  };

  elements.lightboxImage.onerror = function () {
    this.onerror = null;
    this.src = CONFIG.PORTFOLIO.DEFAULT_IMAGE;
    this.classList.add("loaded");
    imageWrapper.classList.remove("loading");
    // Initialise Zoomist even on error
    initialiseZoomist(elements);
  };

  // Set src after handlers
  elements.lightboxImage.src = img.src;

  show(elements.lightbox, "flex");
  document.body.style.overflow = "hidden";
}

/**
 * Close lightbox
 */
function closeLightbox(elements) {
  hide(elements.lightbox);
  document.body.style.overflow = "auto";
  if (sharedZoomist) {
    sharedZoomist.reset();
  }
}

/**
 * Setup lightbox event listeners
 */
function setupLightboxEvents(elements) {
  const closeLightboxHandler = () => closeLightbox(elements);

  elements.closeLightbox?.addEventListener("click", closeLightboxHandler);

  elements.lightbox?.addEventListener("click", (e) => {
    if (e.target === elements.lightbox) {
      closeLightboxHandler();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && elements.lightbox?.style.display === "flex") {
      closeLightboxHandler();
    }
  });
}

/**
 * Initialise Zoomist for the lightbox
 */
function initialiseZoomist(elements) {
  if (elements.zoomistContainer && typeof Zoomist !== 'undefined') {
    // Destroy existing instance if it exists
    if (sharedZoomist) {
      sharedZoomist.destroy();
    }

    // Initialise new Zoomist instance
    sharedZoomist = new Zoomist(elements.zoomistContainer, {
      maxScale: 4,
      bounds: true,
      slider: true,
      zoomer: true
    });
  }
}
