/**
 * Main JavaScript entry point for Peashan Brands website
 * Modular architecture with separation of concerns
 */

// Import all modules
import { initNavigation } from "./modules/navigation.js";
import { initScrollEffects } from "./modules/scroll-effects.js";
import { initPortfolio } from "./modules/portfolio.js";
import { initPartners } from "./modules/partners.js";
import { initForms } from "./modules/forms.js";
import { initWhatsApp } from "./modules/whatsapp.js";
import { initAnimations } from "./modules/animations.js";

/**
 * Initialise all functionality when DOM is ready
 */
document.addEventListener("DOMContentLoaded", () => {
  // Initialise all modules
  initNavigation();
  initScrollEffects();
  initPortfolio();
  initPartners();
  initForms();
  initWhatsApp();
  initAnimations();

    
  const cards = document.querySelectorAll('.services-glass-card');
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.animation = 'serviceCardFadeUp 0.8s ease forwards';
          }, index * 100);
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    cards.forEach(card => {
      observer.observe(card);
      
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-10px) scale(1.02)`;
      });
      
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });

  

});
