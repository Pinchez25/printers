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
      elements.searchInput.value = "";
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
  loadPortfolioItems(elements, state, 1, false);
}

function clearAllFilters(elements, state) {
  if (elements.searchInput) {
    elements.searchInput.value = "";
  }
  state.searchQuery = "";
  hide(elements.searchClear);

  state.filters = [];
  elements.filterBtns.forEach((btn) => btn.classList.remove("active"));

  const allBtn = document.querySelector(
    `.filter-btn[data-filter="${FILTER_ALL}"]`
  );
  if (allBtn) allBtn.classList.add("active");

  applyFilters(elements, state);
}

function handleSeeMore(elements, state) {
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
      state.hasMorePages = data.pagination.has_next;
      state.currentPage = data.pagination.current_page;

      renderPortfolioItems(elements, data.items, append, state);

      toggle(elements.seeMoreContainer, state.hasMorePages, "block");
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
    createPortfolioItemElement(elements.template, item, index)
  );

  const fragment = createFragment(portfolioElements);
  elements.grid.appendChild(fragment);
}

function setupImageLoading(img, wrapper, onLoadCallback) {
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

  div.dataset.category = (item.tags || []).join(" ");
  div.dataset.itemId = item.id ?? "";
  // keep full description in dataset so lightbox can access it without
  // rendering the description node inside the grid
  div.dataset.fullDescription = escapeHtml(
    item.description || CONFIG.PORTFOLIO.DEFAULT_DESCRIPTION
  );
  // store the title on the container so openLightbox can read it even
  // if the title element isn't created in the DOM
  div.dataset.title = item.title || "";
  div.style.setProperty(
    "--animation-delay",
    `${index * ANIMATION_DELAY_MULTIPLIER}s`
  );

  const img = clone.querySelector(".portfolio-image");
  const imgWrapper = clone.querySelector(".portfolio-image-wrapper");

  img.alt = item.title || "";
  setupImageLoading(img, imgWrapper);
  img.src = item.thumbnail || CONFIG.PORTFOLIO.DEFAULT_IMAGE;

  // set overlay title when present in template
  const overlayTitle = clone.querySelector(".portfolio-overlay-title");
  if (overlayTitle) overlayTitle.textContent = item.title || "";

  // store tags as a comma-separated dataset for potential filtering or
  // accessibility use without creating tag elements in the grid
  div.dataset.tags = (item.tags || []).join(",");

  return clone;
}

function displayNoResultsInGrid(elements) {
  elements.grid.innerHTML = "";
  const noResultsContainer = document.createElement('div');
  noResultsContainer.className = 'no-results-container';
  noResultsContainer.innerHTML = `
    <div class="no-results-icon">🔍</div>
    <p class="no-results-text">No projects found</p>
    <button class="btn-secondary clear-filters-btn">Clear Search & Filters</button>
  `;
  elements.grid.appendChild(noResultsContainer);
  const clearBtn = noResultsContainer.querySelector('.clear-filters-btn');
  clearBtn.addEventListener('click', () => {
    clearAllFilters(elements, state);
  });
  hide(elements.controls);
  hide(elements.filters);
  hide(elements.seeMoreContainer);
}

function hideNoResults(elements) {
  show(elements.grid, "grid");
  show(elements.controls, "flex");
  show(elements.filters, "flex");
}

function openLightbox(item, elements) {
  const img = item.querySelector(".portfolio-image");
  // title may not exist as a DOM node inside the grid anymore; prefer
  // the dataset value (set when the element is created) and fall back to
  // a title element if present for compatibility.
  const title = item.dataset.title || item.querySelector(".portfolio-title")?.textContent || "";
  const description = item.dataset.fullDescription || "";
  const imageWrapper = elements.lightboxImage.parentElement;

  elements.lightboxImage.classList.remove("loaded");
  elements.lightboxTitle.textContent = title;
  elements.lightboxDescription.textContent = description;
  elements.lightboxImage.alt = title;

  setupImageLoading(elements.lightboxImage, imageWrapper, () => {
    initialiseZoomist(elements);
  });

  elements.lightboxImage.src = img.src;

  show(elements.lightbox, "flex");
  document.body.style.overflow = "hidden";
}

function closeLightbox(elements) {
  hide(elements.lightbox);
  document.body.style.overflow = "auto";
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
