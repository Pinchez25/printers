import { debounce, escapeHtml } from "./utils.js";
import {
  show,
  hide,
  toggle,
  delegateEvent,
  createFragment,
} from "./dom-utils.js";
import { showNotification } from "./notifications.js";
import { CONFIG } from "../config.js";

const FILTER_ALL = "all";
const ANIMATION_DELAY_MULTIPLIER = 0.1;

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
    this.hasMorePages = true;
  }
}

let sharedZoomist = null;
let searchHandler = null;

export function initPortfolio() {
  const elements = cachePortfolioElements();
  if (!elements.grid) return;

  const state = new PortfolioState();

  loadPortfolioItems(elements, state, 1, false);
  setupPortfolioEvents(elements, state);
  setupLightboxEvents(elements);
}

function cachePortfolioElements() {
  return {
    grid: document.getElementById("portfolioGrid"),
    loading: document.getElementById("portfolioLoading"),
    controls: document.getElementById("portfolio-controls"),
    filters: document.getElementById("portfolio-filters"),
    filterBtns: document.querySelectorAll(".filter-btn"),
    searchInput: document.getElementById("portfolio-search"),
    searchClear: document.getElementById("search-clear"),
    clearFiltersBtn: document.getElementById("clear-search-filters"),
    seeMoreContainer: document.querySelector(".portfolio-see-more"),
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

function setupPortfolioEvents(elements, state) {
  delegateEvent(
    elements.grid?.parentElement,
    ".filter-btn",
    "click",
    (e, btn) => {
      handleFilterClick(btn, elements, state);
    }
  );

  delegateEvent(elements.grid, ".portfolio-item", "click", (e, item) => {
    if (!item.classList.contains("hidden")) {
      openLightbox(item, elements);
    }
  });

  if (elements.searchInput) {
    searchHandler = debounce((e) => {
      state.searchQuery = e.target.value.trim();
      toggle(elements.searchClear, state.searchQuery, "flex");
      applyFilters(elements, state);
    }, CONFIG.ANIMATION.SEARCH_DEBOUNCE);

    elements.searchInput.addEventListener("input", searchHandler);
  }

  if (elements.searchClear) {
    elements.searchClear.addEventListener("click", () => {
      if (elements.searchInput) {
        elements.searchInput.value = "";
      }
      state.searchQuery = "";
      hide(elements.searchClear);
      applyFilters(elements, state);
    });
  }

  if (elements.clearFiltersBtn) {
    elements.clearFiltersBtn.addEventListener("click", () => {
      clearAllFilters(elements, state);
    });
  }

  if (elements.seeMoreBtn) {
    elements.seeMoreBtn.addEventListener("click", () => {
      handleSeeMore(elements, state);
    });
  }

  const allFilterBtn = document.querySelector(
    `.filter-btn[data-filter="${FILTER_ALL}"]`
  );
  if (allFilterBtn) {
    allFilterBtn.classList.add("active");
  }
}

function handleFilterClick(btn, elements, state) {
  const filterValue = btn.dataset.filter;

  if (filterValue === FILTER_ALL) {
    elements.filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.filters = [];
  } else {
    const allBtn = document.querySelector(
      `.filter-btn[data-filter="${FILTER_ALL}"]`
    );
    if (allBtn) allBtn.classList.remove("active");

    if (state.filters.includes(filterValue)) {
      state.filters = state.filters.filter((f) => f !== filterValue);
      btn.classList.remove("active");

      if (state.filters.length === 0 && allBtn) {
        allBtn.classList.add("active");
      }
    } else {
      state.filters.push(filterValue);
      btn.classList.add("active");
    }
  }

  applyFilters(elements, state);
}

function applyFilters(elements, state) {
  state.currentPage = 1;
  state.hasMorePages = true;
  loadPortfolioItems(elements, state, 1, false);
}

function clearAllFilters(elements, state) {
  if (elements.searchInput) {
    elements.searchInput.value = "";
  }
  state.searchQuery = "";
  if (elements.searchClear) {
    hide(elements.searchClear);
  }

  state.filters = [];
  elements.filterBtns.forEach((btn) => btn.classList.remove("active"));

  const allBtn = document.querySelector(
    `.filter-btn[data-filter="${FILTER_ALL}"]`
  );
  if (allBtn) allBtn.classList.add("active");

  applyFilters(elements, state);
}

function handleSeeMore(elements, state) {
  if (!elements.seeMoreText || !elements.seeMoreLoading) return;
  
  hide(elements.seeMoreText);
  show(elements.seeMoreLoading, "block");

  state.currentPage += 1;
  loadPortfolioItems(elements, state, state.currentPage, true).finally(() => {
    show(elements.seeMoreText, "inline");
    hide(elements.seeMoreLoading);
  });
}

async function loadPortfolioItems(elements, state, page = 1, append = false) {
  if (state.isLoading) return;

  state.isLoading = true;
  if (!append && elements.loading) {
    show(elements.loading, "flex");
  }

  try {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(CONFIG.PORTFOLIO.ITEMS_PER_PAGE),
      search: state.searchQuery,
    });

    if (state.filters.length > 0) {
      params.set("tags", state.filters.join(","));
    }

    const response = await fetch(
      `${CONFIG.PORTFOLIO.API_ENDPOINT}?${params}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      state.hasMorePages = data.pagination?.has_next ?? false;
      state.currentPage = data.pagination?.current_page ?? page;

      renderPortfolioItems(elements, data.items || [], append, state);

      if (elements.seeMoreContainer) {
        toggle(elements.seeMoreContainer, state.hasMorePages, "block");
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
    
    if (!append) {
      elements.grid.innerHTML = "";
      displayErrorState(elements, state);
    }
  } finally {
    state.isLoading = false;
    if (elements.loading) {
      hide(elements.loading);
    }
  }
}

function renderPortfolioItems(elements, items, append = false, state) {
  if (!append) {
    elements.grid.innerHTML = "";
  }

  if (items.length === 0) {
    displayNoResultsInGrid(elements, state);
    return;
  }

  hideNoResults(elements);

  const portfolioElements = items.map((item, index) =>
    createPortfolioItemElement(elements.template, item, append ? index + (state.currentPage - 1) * CONFIG.PORTFOLIO.ITEMS_PER_PAGE : index)
  );

  const fragment = createFragment(portfolioElements);
  elements.grid.appendChild(fragment);
}

function setupImageLoading(img, wrapper, onLoadCallback) {
  if (!wrapper) return;
  
  wrapper.classList.add("loading");

  img.onload = function () {
    this.classList.add("loaded");
    wrapper.classList.remove("loading");
    if (onLoadCallback) onLoadCallback();
  };

  img.onerror = function () {
    this.onerror = null;
    this.src = CONFIG.PORTFOLIO.DEFAULT_IMAGE;
    this.classList.add("loaded");
    wrapper.classList.remove("loading");
    if (onLoadCallback) onLoadCallback();
  };
}

function createPortfolioItemElement(template, item, index) {
  if (!template) {
    console.error("Portfolio template not found");
    return document.createElement("div");
  }

  const clone = template.content.cloneNode(true);
  const div = clone.querySelector(".portfolio-item");

  if (div) {
    div.dataset.category = (item.tags || []).join(" ");
    div.dataset.itemId = String(item.id ?? "");
    div.dataset.fullDescription = escapeHtml(
      item.description || CONFIG.PORTFOLIO.DEFAULT_DESCRIPTION
    );
    div.dataset.title = item.title || "";
    div.dataset.tags = (item.tags || []).join(",");
    div.style.setProperty(
      "--animation-delay",
      `${index * ANIMATION_DELAY_MULTIPLIER}s`
    );
  }

  const img = clone.querySelector(".portfolio-image");
  const imgWrapper = clone.querySelector(".portfolio-image-wrapper");

  if (img && imgWrapper) {
    img.alt = item.title || "";
    setupImageLoading(img, imgWrapper);
    img.src = item.thumbnail || CONFIG.PORTFOLIO.DEFAULT_IMAGE;
  }

  const overlayTitle = clone.querySelector(".portfolio-overlay-title");
  if (overlayTitle) overlayTitle.textContent = item.title || "";

  return clone;
}

function displayNoResultsInGrid(elements, state) {
  elements.grid.innerHTML = "";
  const noResultsContainer = document.createElement("div");
  noResultsContainer.className = "no-results-container";
  noResultsContainer.innerHTML = `
    <div class="no-results-icon">🔍</div>
    <p class="no-results-text">No projects found</p>
    <button class="btn-secondary clear-filters-btn">Clear Search & Filters</button>
  `;
  elements.grid.appendChild(noResultsContainer);
  
  const clearBtn = noResultsContainer.querySelector(".clear-filters-btn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      clearAllFilters(elements, state);
    });
  }
  
  if (elements.controls) hide(elements.controls);
  if (elements.filters) hide(elements.filters);
  if (elements.seeMoreContainer) hide(elements.seeMoreContainer);
}

function displayErrorState(elements, state) {
  const errorContainer = document.createElement("div");
  errorContainer.className = "error-container";
  errorContainer.innerHTML = `
    <div class="error-icon">⚠️</div>
    <p class="error-text">Unable to load portfolio items</p>
    <button class="btn-primary retry-btn">Retry</button>
  `;
  elements.grid.appendChild(errorContainer);
  
  const retryBtn = errorContainer.querySelector(".retry-btn");
  if (retryBtn) {
    retryBtn.addEventListener("click", () => {
      loadPortfolioItems(elements, state, state.currentPage, false);
    });
  }
}

function hideNoResults(elements) {
  show(elements.grid, "grid");
  if (elements.controls) show(elements.controls, "flex");
  if (elements.filters) show(elements.filters, "flex");
}

function openLightbox(item, elements) {
  const img = item.querySelector(".portfolio-image");
  const title = item.dataset.title || item.querySelector(".portfolio-title")?.textContent || "";
  const description = item.dataset.fullDescription || "";
  const imageWrapper = elements.lightboxImage?.parentElement;

  if (elements.lightboxImage) {
    elements.lightboxImage.classList.remove("loaded");
    elements.lightboxImage.alt = title;
    
    if (imageWrapper) {
      setupImageLoading(elements.lightboxImage, imageWrapper, () => {
        initialiseZoomist(elements);
      });
    }
    
    if (img) {
      elements.lightboxImage.src = img.src;
    }
  }
  
  if (elements.lightboxTitle) elements.lightboxTitle.textContent = title;
  if (elements.lightboxDescription) elements.lightboxDescription.textContent = description;

  if (elements.lightbox) show(elements.lightbox, "flex");
  document.body.style.overflow = "hidden";
}

function closeLightbox(elements) {
  if (elements.lightbox) {
    hide(elements.lightbox);
  }
  document.body.style.overflow = "";
  if (sharedZoomist) {
    sharedZoomist.reset();
  }
}

function setupLightboxEvents(elements) {
  const closeLightboxHandler = () => closeLightbox(elements);

  if (elements.closeLightbox) {
    elements.closeLightbox.addEventListener("click", closeLightboxHandler);
  }

  if (elements.lightbox) {
    elements.lightbox.addEventListener("click", (e) => {
      if (e.target === elements.lightbox) {
        closeLightboxHandler();
      }
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && elements.lightbox?.style.display === "flex") {
      closeLightboxHandler();
    }
  });
}

function initialiseZoomist(elements) {
  if (elements.zoomistContainer && typeof Zoomist !== "undefined") {
    if (sharedZoomist) {
      sharedZoomist.destroy();
      sharedZoomist = null;
    }

    sharedZoomist = new Zoomist(elements.zoomistContainer, {
      maxScale: 4,
      bounds: true,
      slider: true,
      zoomer: true,
    });
  }
}
