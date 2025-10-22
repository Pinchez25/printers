/**
 * Navigation functionality module
 */
import { throttle } from "./utils.js";
import {
  toggle,
  toggleClass,
  scrollToElement,
  getOffsetTop,
} from "./dom-utils.js";
import { CONFIG } from "../config.js";

/**
 * Initialise navigation functionality
 */
export function initNavigation() {
  const nav = document.querySelector("nav");
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");

  if (!nav || !mobileMenuBtn || !mobileMenu) return;

  const navHeight = nav.offsetHeight;

  // Handle scroll to add/remove scrolled class
  const handleScroll = throttle(() => {
    toggleClass(
      nav,
      "scrolled",
      window.scrollY > CONFIG.ANIMATION.SCROLL_THRESHOLD
    );
  }, CONFIG.ANIMATION.THROTTLE_DELAY);

  // Handle window resize to close mobile menu on desktop
  const handleResize = throttle(() => {
    if (window.innerWidth > CONFIG.RESPONSIVE.MOBILE_BREAKPOINT) {
      mobileMenu.classList.add("hidden");
      mobileMenu.style.display = "none";
      mobileMenuBtn.setAttribute("data-icon", "hamburger");
    }
  }, CONFIG.ANIMATION.THROTTLE_DELAY);

  // Add event listeners
  window.addEventListener("scroll", handleScroll, { passive: true });
  window.addEventListener("resize", handleResize, { passive: true });

  // Mobile menu toggle
  mobileMenuBtn.addEventListener("click", () => {
    const isVisible = mobileMenu.style.display === "block";
    mobileMenu.style.display = isVisible ? "none" : "block";
    mobileMenuBtn.setAttribute("data-icon", isVisible ? "hamburger" : "close");
  });

  // Smooth scroll for navigation links
  document.addEventListener("click", (e) => {
    const link = e.target.closest(".nav-link, .mobile-menu-link");
    if (!link) return;

    e.preventDefault();
    const targetId = link.getAttribute("href");
    const targetSection = document.querySelector(targetId);

    if (!targetSection) return;

    scrollToElement(targetSection, navHeight);

    // Close mobile menu if open
    if (mobileMenu.style.display === "block") {
      mobileMenu.style.display = "none";
      mobileMenuBtn.setAttribute("data-icon", "hamburger");
    }
  });
}
