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
});
