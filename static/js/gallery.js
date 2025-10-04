(function () {
  "use strict";

  const CONFIG = window.GALLERY_CONFIG || {};
  const API_ENDPOINT = CONFIG.apiEndpoint || "";
  const TAGS_API_ENDPOINT = CONFIG.tagsApiEndpoint || "";
  const DEFAULT_IMG = CONFIG.defaultImage || "";
  const ITEMS_PER_PAGE = Number(CONFIG.itemsPerPage || 6);

  const state = {
    currentImages: [],
    selectedTags: ["all"],
    isLoading: false,
    currentPage: 1,
    hasNextPage: true,
    searchDebounceTimer: null,
    testimonialInterval: null,
    currentTestimonial: 0,
    observers: {
      sentinel: null,
      animation: null,
      mutation: null,
      lazyLoad: null
    }
  };

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    if (!API_ENDPOINT || !TAGS_API_ENDPOINT) {
      return;
    }

    loadFilterTags();
    loadGalleryItems();
    setupEventDelegation();
    startTestimonialCarousel();
    setupInfiniteScroll();
    setupScrollEffects();

    setTimeout(() => {
      if (window.lightbox) {
        window.lightbox.refresh();
      }
    }, 100);
  }

  async function loadFilterTags() {
    const tagsLoading = document.getElementById("tagsLoading");
    if (tagsLoading) {
      tagsLoading.style.display = "inline-block";
    }

    try {
      const response = await fetch(TAGS_API_ENDPOINT);
      const data = await response.json();

      if (data.success && data.tags && data.tags.length > 0) {
        const filterTagsContainer = document.getElementById("filterTags");
        if (filterTagsContainer) {
          const allTag = filterTagsContainer.querySelector('.filter-tag[data-tag="all"]');
          const fragment = document.createDocumentFragment();

          data.tags.forEach((tag) => {
            const tagElement = document.createElement("span");
            tagElement.className = "filter-tag";
            tagElement.setAttribute(
              "data-tag",
              tag.slug || String(tag.name || "").toLowerCase().replace(/\s+/g, "-")
            );
            tagElement.textContent = tag.name;
            tagElement.title = `${tag.name} (${tag.count || 0} items)`;
            fragment.appendChild(tagElement);
          });

          if (allTag && allTag.nextSibling) {
            allTag.parentNode.insertBefore(fragment, allTag.nextSibling);
          } else if (filterTagsContainer) {
            filterTagsContainer.appendChild(fragment);
          }
        }
      } else {
        const noTagsElement = document.getElementById("noTags");
        if (noTagsElement) {
          noTagsElement.style.display = "inline-block";
        }
      }
    } catch (error) {
      console.error("Error loading filter tags:", error);
    } finally {
      if (tagsLoading) {
        tagsLoading.style.display = "none";
      }
    }
  }

  function setupInfiniteScroll() {
    const sentinel = document.getElementById("infiniteScrollSentinel");
    const loadMoreBtn = document.getElementById("loadMoreBtn");

    if ("IntersectionObserver" in window && sentinel) {
      if (loadMoreBtn) loadMoreBtn.style.display = "none";

      disconnectObserver('sentinel');

      state.observers.sentinel = new IntersectionObserver(
        (entries) => {
          const entry = entries[0];
          if (entry && entry.isIntersecting && !state.isLoading && state.hasNextPage) {
            state.currentPage++;
            showLoadingSpinner();
            loadGalleryItems(true, false);
          }
        },
        { root: null, rootMargin: "200px 0px", threshold: 0 }
      );
      state.observers.sentinel.observe(sentinel);
    } else if (loadMoreBtn) {
      loadMoreBtn.style.display = "block";
    }
  }

  async function loadGalleryItems(append = false, resetPagination = true) {
    if (state.isLoading) return;
    state.isLoading = true;

    if (resetPagination) {
      state.currentPage = 1;
      state.hasNextPage = true;
      setupInfiniteScroll();
    }

    const searchInput = document.getElementById("searchInput");
    const searchTerm = searchInput ? searchInput.value.trim() : "";

    const params = new URLSearchParams({
      page: String(state.currentPage),
      per_page: String(ITEMS_PER_PAGE),
      search: searchTerm,
    });

    if (state.selectedTags.length > 0) {
      state.selectedTags.forEach((tag) => {
        if (tag !== "all") {
          const apiTag = tag.replace(/-/g, " ");
          params.append("tags[]", apiTag);
        }
      });
    }

    try {
      const response = await fetch(`${API_ENDPOINT}?${params.toString()}`);
      const data = await response.json();

      if (data.success) {
        if (!append) {
          const galleryGrid = document.getElementById("galleryGrid");
          const noResultsMessage = document.getElementById("noResultsMessage");
          if (galleryGrid) galleryGrid.innerHTML = "";
          if (noResultsMessage) noResultsMessage.style.display = "none";
          state.currentImages = [];
        }

        if (!data.items || data.items.length === 0) {
          showNoResultsMessage();
          state.hasNextPage = false;
          disconnectObserver('sentinel');
          updateLoadMoreButton();
          state.isLoading = false;
          return;
        }

        state.currentImages.push(...data.items);

        const galleryGrid = document.getElementById("galleryGrid");
        if (galleryGrid && data.items.length > 0) {
          const fragment = document.createDocumentFragment();
          data.items.forEach((item, index) => {
            const galleryItem = createGalleryItem(
              item,
              state.currentImages.length - data.items.length + index
            );
            fragment.appendChild(galleryItem);
          });

          galleryGrid.appendChild(fragment);
        }

        state.currentPage = data.pagination.current_page;
        state.hasNextPage = data.pagination.has_next;

        if (!state.hasNextPage) {
          disconnectObserver('sentinel');
        }

        updateLoadMoreButton(data.pagination);

        // Debug pagination info with filters
        console.log("Pagination Info:", {
          currentPage: data.pagination.current_page,
          totalPages: data.pagination.total_pages,
          hasNext: data.pagination.has_next,
          itemsLoaded: data.items.length,
          totalItemsInDB: data.pagination.total_items || 'Not provided by API'
        });
        console.log("Filters Applied:", {
          search: data.filters.search || 'None',
          tags: data.filters.tags.length > 0 ? data.filters.tags : 'None'
        });

        setTimeout(() => {
          setupLazyLoading();
          state.isLoading = false;
          hideLoadingSpinner();

          if (window.lightbox) {
            window.lightbox.refresh();
          }
        }, 100);
      } else {
        console.error("Failed to load gallery items:", data.message);
        showNoResultsMessage("Failed to load gallery items. Please try again.");
        state.isLoading = false;
      }
    } catch (error) {
      console.error("Error loading gallery items:", error);
      state.isLoading = false;
    }
  }

  function showNoResultsMessage(customMessage = null) {
    const galleryGrid = document.getElementById("galleryGrid");
    const noResultsMessage = document.getElementById("noResultsMessage");
    const noResultsText = document.getElementById("noResultsText");

    if (galleryGrid) galleryGrid.innerHTML = "";
    if (noResultsMessage) noResultsMessage.style.display = "block";
    if (noResultsText && customMessage) {
      noResultsText.textContent = customMessage;
    }

    const loadMoreBtn = document.getElementById("loadMoreBtn");
    if (loadMoreBtn) loadMoreBtn.style.display = "none";
  }

  function updateLoadMoreButton(pagination = null) {
    const loadMoreBtn = document.getElementById("loadMoreBtn");
    const hasSentinel = document.getElementById("infiniteScrollSentinel");
    const supportsIO = typeof IntersectionObserver !== "undefined";

    if (!loadMoreBtn) return;

    if (supportsIO && hasSentinel) {
      loadMoreBtn.style.display = "none";
      return;
    }

    if (pagination) {
      if (pagination.has_next) {
        loadMoreBtn.style.display = "block";
        loadMoreBtn.innerHTML = `<i class="fas fa-plus mr-2"></i> Load More (${pagination.current_page}/${pagination.total_pages})`;
      } else {
        loadMoreBtn.style.display = "none";
      }
    } else {
      loadMoreBtn.style.display = state.hasNextPage ? "block" : "none";
      loadMoreBtn.innerHTML = `<i class="fas fa-plus mr-2"></i> Load More`;
    }
  }

  function createGalleryItem(item, index) {
    const tpl = document.getElementById("galleryItemTemplate");
    if (!tpl || !tpl.content || !tpl.content.firstElementChild) {
      console.error("Gallery item template not found");
      return document.createElement("div");
    }

    const node = tpl.content.firstElementChild.cloneNode(true);

    const itemEl = node.querySelector(".gallery-item");
    if (itemEl) itemEl.setAttribute("data-src", item.fullImage || "");

    const imgEl = node.querySelector("img.lazy-image");
    if (imgEl) {
      imgEl.setAttribute("data-src", item.thumbnail || "");
      imgEl.setAttribute("alt", String(item.title || ""));
    }

    const titleEl = node.querySelector(".gallery-title");
    if (titleEl) titleEl.textContent = String(item.title || "");

    const descEl = node.querySelector(".gallery-desc");
    if (descEl) descEl.textContent = String(item.description || "");

    const tagsContainer = node.querySelector(".gallery-card-tags");
    if (tagsContainer) {
      tagsContainer.innerHTML = "";
      (item.tags || []).forEach((tag) => {
        const span = document.createElement("span");
        span.className = "gallery-tag";
        span.textContent = String(tag);
        tagsContainer.appendChild(span);
      });
    }

    return node;
  }

  function setupLazyLoading() {
    const lazyImages = document.querySelectorAll(".lazy-image:not(.loaded)");

    const onImageError = (img) => {
      if (DEFAULT_IMG && img.src !== DEFAULT_IMG) {
        img.onerror = null;
        img.src = DEFAULT_IMG;
      }
      img.style.opacity = "1";
      img.classList.add("error-fallback");
    };

    if ("IntersectionObserver" in window) {
      if (!state.observers.lazyLoad) {
        state.observers.lazyLoad = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove("image-skeleton");
                img.classList.add("loaded");
                state.observers.lazyLoad.unobserve(img);

                img.onload = () => {
                  img.style.opacity = "1";
                };

                img.onerror = () => onImageError(img);
              }
            });
          },
          { threshold: 0.1, rootMargin: "50px" }
        );
      }

      lazyImages.forEach((img) => {
        img.style.opacity = "0";
        img.style.transition = "opacity 0.3s ease";
        state.observers.lazyLoad.observe(img);
      });
    } else {
      lazyImages.forEach((img) => {
        img.src = img.dataset.src;
        img.classList.remove("image-skeleton");
        img.classList.add("loaded");
        img.onerror = () => onImageError(img);
      });
    }
  }

  function setupEventDelegation() {
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", handleSearchInput);
    }

    const filterTagsContainer = document.getElementById("filterTags");
    if (filterTagsContainer) {
      filterTagsContainer.addEventListener("click", handleFilterTagClick);
    }

    const loadMoreBtn = document.getElementById("loadMoreBtn");
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener("click", handleLoadMoreClick);
    }

    const clearFiltersBtn = document.getElementById("clearFilters");
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener("click", clearAllFilters);
    }

    const clearAllFiltersBtn = document.getElementById("clearAllFiltersBtn");
    if (clearAllFiltersBtn) {
      clearAllFiltersBtn.addEventListener("click", clearAllFilters);
    }
  }

  function handleSearchInput() {
    clearTimeout(state.searchDebounceTimer);
    state.searchDebounceTimer = setTimeout(() => {
      loadGalleryItems(false, true);
    }, 300);
  }

  function handleFilterTagClick(e) {
    const tag = e.target.closest(".filter-tag");
    if (!tag) return;

    const tagValue = tag.dataset.tag;

    if (tagValue === "all") {
      document.querySelectorAll(".filter-tag").forEach((t) => {
        t.classList.remove("active", "selected");
      });
      tag.classList.add("active");
      state.selectedTags = ["all"];
    } else {
      const allTag = document.querySelector('.filter-tag[data-tag="all"]');
      if (allTag) allTag.classList.remove("active");

      if (state.selectedTags.includes(tagValue)) {
        state.selectedTags = state.selectedTags.filter((t) => t !== tagValue);
        tag.classList.remove("selected");
      } else {
        state.selectedTags.push(tagValue);
        tag.classList.add("selected");
      }

      if (
        state.selectedTags.length === 0 ||
        (state.selectedTags.length === 1 && state.selectedTags[0] === "all")
      ) {
        if (allTag) allTag.classList.add("active");
        state.selectedTags = ["all"];
        document.querySelectorAll(".filter-tag").forEach((t) => t.classList.remove("selected"));
      }
    }

    loadGalleryItems(false, true);
  }

  function handleLoadMoreClick() {
    if (!state.isLoading && state.hasNextPage) {
      state.currentPage++;
      loadGalleryItems(true, false);
    }
  }

  function clearAllFilters() {
    const searchInput = document.getElementById("searchInput");
    if (searchInput) searchInput.value = "";

    document.querySelectorAll(".filter-tag").forEach((t) => {
      t.classList.remove("active", "selected");
    });

    const allTag = document.querySelector('.filter-tag[data-tag="all"]');
    if (allTag) allTag.classList.add("active");

    state.selectedTags = ["all"];
    loadGalleryItems(false, true);
  }

  function startTestimonialCarousel() {
    const testimonials = document.querySelectorAll(".testimonial-item");
    const dots = document.querySelectorAll(".testimonial-dot");
    const totalTestimonials = testimonials.length;

    if (totalTestimonials === 0) return;

    function showTestimonial(index) {
      testimonials.forEach((item) => item.classList.remove("active"));
      dots.forEach((dot) => dot.classList.remove("active"));

      if (testimonials[index]) testimonials[index].classList.add("active");
      if (dots[index]) dots[index].classList.add("active");
    }

    function nextTestimonial() {
      state.currentTestimonial = (state.currentTestimonial + 1) % totalTestimonials;
      showTestimonial(state.currentTestimonial);
    }

    function startInterval() {
      if (state.testimonialInterval) {
        clearInterval(state.testimonialInterval);
      }
      state.testimonialInterval = setInterval(nextTestimonial, 5000);
    }

    function stopInterval() {
      if (state.testimonialInterval) {
        clearInterval(state.testimonialInterval);
        state.testimonialInterval = null;
      }
    }

    startInterval();

    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => {
        stopInterval();
        state.currentTestimonial = index;
        showTestimonial(state.currentTestimonial);
        setTimeout(startInterval, 10000);
      });
    });

    const carousel = document.querySelector(".testimonial-carousel");
    if (carousel) {
      carousel.addEventListener("mouseenter", stopInterval);
      carousel.addEventListener("mouseleave", startInterval);
    }
  }

  function setupAnimationObserver() {
    if (state.observers.animation) return;

    state.observers.animation = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animated");
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    document.querySelectorAll(".animate-on-scroll").forEach((element) => {
      state.observers.animation.observe(element);
    });

    const galleryGrid = document.getElementById("galleryGrid");
    if (galleryGrid && !state.observers.mutation) {
      state.observers.mutation = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              if (node.classList && node.classList.contains("animate-on-scroll")) {
                state.observers.animation.observe(node);
              }
              const animatedChildren = node.querySelectorAll && node.querySelectorAll(".animate-on-scroll");
              if (animatedChildren) {
                animatedChildren.forEach((child) => state.observers.animation.observe(child));
              }
            }
          });
        });
      });

      state.observers.mutation.observe(galleryGrid, {
        childList: true,
        subtree: true,
      });
    }
  }

  function setupScrollEffects() {
    setupAnimationObserver();
  }

  function disconnectObserver(observerName) {
    if (state.observers[observerName]) {
      try {
        state.observers[observerName].disconnect();
      } catch (error) {
        console.error(`Error disconnecting ${observerName} observer:`, error);
      }
    }
  }

  function showLoadingSpinner() {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) {
      spinner.style.display = "block";
    }
  }

  function hideLoadingSpinner() {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) {
      spinner.style.display = "none";
    }
  }

  function cleanup() {
    if (state.testimonialInterval) {
      clearInterval(state.testimonialInterval);
    }
    if (state.searchDebounceTimer) {
      clearTimeout(state.searchDebounceTimer);
    }
    Object.keys(state.observers).forEach(disconnectObserver);
  }

  window.addEventListener("beforeunload", cleanup);

  window.debugGallery = function () {
    return {
      selectedTags: state.selectedTags.slice(),
      page: state.currentPage,
      hasNext: state.hasNextPage,
      perPage: ITEMS_PER_PAGE,
      endpoints: { API_ENDPOINT, TAGS_API_ENDPOINT },
    };
  };
})();