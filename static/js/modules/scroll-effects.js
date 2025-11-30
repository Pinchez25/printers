/**
 * Scroll effects and animations module
 */
import { throttle } from "./utils.js";

/**
 * Initialise scroll effects and animations
 */
export function initScrollEffects() {
  initIntersectionObserver();
}

/**
 * Initialise intersection observer for scroll animations
 */
function initIntersectionObserver() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay) || 0;
        
        setTimeout(() => {
          entry.target.classList.add("animate");
        }, delay);
        
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  const animatedElements = document.querySelectorAll("[data-animate]");
  animatedElements.forEach((el) => {
    observer.observe(el);
  });
}
