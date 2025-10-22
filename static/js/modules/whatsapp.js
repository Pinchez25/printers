/**
 * WhatsApp functionality module
 */
import { toggle } from "./dom-utils.js";
import { showNotification } from "./notifications.js";

/**
 * Initialise WhatsApp functionality
 */
export function initWhatsApp() {
  const whatsappFloat = document.getElementById("whatsapp-float");
  const whatsappModal = document.getElementById("whatsapp-modal");
  const whatsappModalClose = document.getElementById("whatsapp-modal-close");
  const whatsappForm = document.getElementById("whatsapp-form");

  if (!whatsappFloat || !whatsappModal) return;

  // Toggle modal on float button click
  whatsappFloat.addEventListener("click", () => {
    // Don't open modal if no contact number configured
    if (!window.config || !window.config.contact_number) return;

    const isVisible = whatsappModal.style.display === "block";
    whatsappModal.style.display = isVisible ? "none" : "block";
  });

  // Close modal button
  whatsappModalClose?.addEventListener("click", () => {
    whatsappModal.style.display = "none";
  });

  // Handle form submission
  whatsappForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    handleWhatsAppSubmit();
  });

  // Close modal when clicking outside
  document.addEventListener("click", (e) => {
    if (
      !whatsappFloat?.contains(e.target) &&
      !whatsappModal?.contains(e.target)
    ) {
      whatsappModal.style.display = "none";
    }
  });
}

/**
 * Handle WhatsApp form submission
 */
function handleWhatsAppSubmit() {
  const messageField = document.getElementById("whatsapp-message");
  const whatsappModal = document.getElementById("whatsapp-modal");
  const whatsappForm = document.getElementById("whatsapp-form");

  const message = messageField?.value.trim();

  if (!message) {
    showNotification("Please enter a message", "error");
    return;
  }

  if (!window.config || !window.config.contact_number) {
    showNotification("WhatsApp contact not configured", "error");
    return;
  }

  const phoneNumber = window.config.contact_number.replace(/\D/g, "");
  const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(
    message
  )}`;

  window.open(whatsappUrl, "_blank");

  if (whatsappModal) {
    whatsappModal.style.display = "none";
  }

  if (whatsappForm) {
    whatsappForm.reset();
  }
}
