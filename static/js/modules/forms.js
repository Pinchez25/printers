/**
 * Form handling module
 */
import { getCSRFToken, isValidEmail } from "./utils.js";
import { scrollToElement } from "./dom-utils.js";
import { showNotification } from "./notifications.js";

/**
 * Initialise form functionality
 */
export function initForms() {
  const contactForm = document.querySelector(".contact-form");
  const viewWorkBtn = document.getElementById("view-work-btn");
  const getQuoteBtn = document.getElementById("get-quote-btn");
  const nav = document.querySelector("nav");
  const navHeight = nav?.offsetHeight || 0;

  // Scroll to section buttons
  viewWorkBtn?.addEventListener("click", () => {
    const section = document.querySelector("#portfolio");
    if (section) scrollToElement(section, navHeight);
  });

  getQuoteBtn?.addEventListener("click", () => {
    const section = document.querySelector("#contact");
    if (section) scrollToElement(section, navHeight);
  });

  // Contact form submission
  contactForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleContactFormSubmit(contactForm);
  });
}

/**
 * Handle contact form submission
 */
async function handleContactFormSubmit(form) {
  const formData = new FormData(form);
  const submitBtn = form.querySelector('[type="submit"]');

  // Validate required fields
  const requiredFields = ["name", "message"];
  const missingFields = requiredFields.filter(
    (field) => !formData.get(field)?.toString().trim()
  );

  if (missingFields.length > 0) {
    showNotification("Please fill in your name and message", "error");
    return;
  }

  // Ensure either email or phone is provided
  const email = (formData.get("email") || "").toString().trim();
  const phone = (formData.get("phone") || "").toString().trim();

  if (!email && !phone) {
    showNotification(
      "Please provide either an email address or a phone number",
      "error"
    );
    return;
  }

  // Validate email if provided
  if (email && !isValidEmail(email)) {
    showNotification("Please enter a valid email address", "error");
    return;
  }

  // Default service to 'other' if not selected
  if (!(formData.get("service") || "").toString().trim()) {
    formData.set("service", "other");
  }

  // Show loading state
  setButtonLoading(submitBtn, true);

  try {
    const action = form.getAttribute("action") || "/contact/";
    const csrftoken = getCSRFToken();

    const response = await fetch(action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrftoken || "",
      },
      body: formData,
    });

    const data = await response.json().catch(() => ({}));

    if (response.ok && data.success !== false) {
      showNotification(
        data.message || "Thank you! We'll get back to you shortly.",
        "success"
      );
      form.reset();
    } else {
      showNotification(
        data.message || "Failed to submit form. Please try again later.",
        "error"
      );
    }
  } catch (error) {
    console.error("Contact form submit error", error);
    showNotification(
      "There was an error submitting the form. Please try again later.",
      "error"
    );
  } finally {
    setButtonLoading(submitBtn, false);
  }
}

/**
 * Set button loading state using CSS classes
 */
function setButtonLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle("btn-loading", loading);
  btn.setAttribute("aria-busy", loading.toString());
}
