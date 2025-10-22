/**
 * Scroll effects and animations module
 */
import { throttle } from "./utils.js";

/**
 * Initialise scroll effects and animations
 */
export function initScrollEffects() {
  // Intersection Observer for animated elements
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

  // Observe service cards, portfolio items, and contact cards
  const animatedElements = document.querySelectorAll(
    ".service-card, .portfolio-item, .contact-card"
  );

  animatedElements.forEach((el, index) => {
    el.classList.add("animate-out");
    el.style.setProperty("--transition-delay", `${index * 0.1}s`);
    observer.observe(el);
  });

  // Portfolio items observer with animation delay
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
  portfolioItems.forEach((item) => {
    portfolioObserver.observe(item);
  });

  // Parallax background effect
  initParallaxBackground();
}

/**
 * Initialise parallax background effect
 */
function initParallaxBackground() {
  const bgElement1 = document.getElementById("bg-element-1");
  if (!bgElement1) return;

  let mouseX = 0;
  let mouseY = 0;
  let currentX = 0;
  let currentY = 0;

  const handleMouseMove = throttle((e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 50;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 50;
  }, 16);

  document.addEventListener("mousemove", handleMouseMove, { passive: true });

  function animateBackground() {
    currentX += (mouseX - currentX) * 0.05;
    currentY += (mouseY - currentY) * 0.05;
    bgElement1.style.transform = `translate(${currentX}px, ${currentY}px)`;
    requestAnimationFrame(animateBackground);
  }

  animateBackground();
}
