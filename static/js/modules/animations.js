/**
 * Animation effects module
 */

/**
 * Initialise animation effects
 */
export function initAnimations() {
  const serviceCards = document.querySelectorAll(".service-card");

  serviceCards.forEach((card) => {
    const icon = card.querySelector(".service-icon");

    card.addEventListener("mouseenter", () => {
      if (icon) {
        icon.classList.add("bounce-animation");
      }
    });

    card.addEventListener("mouseleave", () => {
      if (icon) {
        icon.classList.remove("bounce-animation");
      }
    });
  });
}
