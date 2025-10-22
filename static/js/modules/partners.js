/**
 * Partners carousel functionality module
 */
import { throttle } from "./utils.js";
import { CONFIG } from "../config.js";

/**
 * Initialise partners carousel
 */
export function initPartners() {
  const partnerItems = document.querySelectorAll(".partner-item");
  const dots = document.querySelectorAll(".partners-dots .dot");
  const itemCount = partnerItems.length;

  if (itemCount === 0) return;

  let currentIndex = 0;
  let autoAdvanceInterval;

  /**
   * Get responsive position configurations
   */
  function getResponsivePositions() {
    const isMobile =
      window.innerWidth <= CONFIG.RESPONSIVE.SMALL_MOBILE_BREAKPOINT;
    const isTablet =
      window.innerWidth <= CONFIG.RESPONSIVE.MOBILE_BREAKPOINT &&
      window.innerWidth > CONFIG.RESPONSIVE.SMALL_MOBILE_BREAKPOINT;

    if (isMobile) {
      return [
        { translateX: 0, scale: 1.1, opacity: 1, zIndex: 7 },
        { translateX: 75, scale: 0.9, opacity: 0.6, zIndex: 6 },
        { translateX: -75, scale: 0.9, opacity: 0.6, zIndex: 6 },
        { translateX: 150, scale: 0.6, opacity: 0.3, zIndex: 5 },
        { translateX: -150, scale: 0.6, opacity: 0.3, zIndex: 5 },
        { translateX: 225, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: -225, scale: 0.4, opacity: 0.15, zIndex: 4 },
        { translateX: 0, scale: 0.2, opacity: 0, zIndex: 1 },
        { translateX: 0, scale: 0.1, opacity: 0, zIndex: 1 },
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
        { translateX: 0, scale: 0.2, opacity: 0, zIndex: 1 },
        { translateX: 0, scale: 0.1, opacity: 0, zIndex: 1 },
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

  /**
   * Get position for a specific relative index
   */
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

  /**
   * Update carousel positions
   */
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

  /**
   * Start auto-advance
   */
  function startAutoAdvance() {
    stopAutoAdvance();
    autoAdvanceInterval = setInterval(() => {
      currentIndex = (currentIndex + 1) % itemCount;
      updateCarousel();
    }, CONFIG.CAROUSEL.AUTO_ADVANCE_INTERVAL);
  }

  /**
   * Stop auto-advance
   */
  function stopAutoAdvance() {
    if (autoAdvanceInterval) {
      clearInterval(autoAdvanceInterval);
      autoAdvanceInterval = null;
    }
  }

  // Event listeners for dots
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

  // Initialise carousel
  updateCarousel(false);
  startAutoAdvance();

  // Update on window resize
  window.addEventListener(
    "resize",
    throttle(() => {
      updateCarousel(false);
    }, CONFIG.ANIMATION.THROTTLE_DELAY)
  );
}
