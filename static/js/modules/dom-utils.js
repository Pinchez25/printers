/**
 * DOM manipulation utility functions
 */

/**
 * Show an element by removing hidden class
 * @param {HTMLElement} element - Element to show
 * @param {string} displayType - Display type (default: 'block')
 */
export function show(element, displayType = 'block') {
  if (!element) return;
  element.classList.remove('hidden');
  element.style.display = displayType;
}

/**
 * Hide an element by adding hidden class
 * @param {HTMLElement} element - Element to hide
 */
export function hide(element) {
  if (!element) return;
  element.classList.add('hidden');
  element.style.display = 'none';
}

/**
 * Toggle element visibility based on condition
 * @param {HTMLElement} element - Element to toggle
 * @param {boolean} condition - Show if true, hide if false
 * @param {string} displayType - Display type when showing
 */
export function toggle(element, condition, displayType = 'block') {
  if (!element) return;
  if (condition) {
    show(element, displayType);
  } else {
    hide(element);
  }
}

/**
 * Toggle a CSS class based on condition
 * @param {HTMLElement} element - Element to modify
 * @param {string} className - Class name to toggle
 * @param {boolean} condition - Add if true, remove if false
 */
export function toggleClass(element, className, condition) {
  if (!element) return;
  element.classList.toggle(className, condition);
}

/**
 * Set display property directly
 * @param {HTMLElement} element - Element to modify
 * @param {string} displayValue - Display value
 */
export function setDisplay(element, displayValue) {
  if (!element) return;
  element.style.display = displayValue;
}

/**
 * Delegate event handling to parent element
 * @param {HTMLElement} parent - Parent element
 * @param {string} selector - Child selector
 * @param {string} eventType - Event type
 * @param {Function} handler - Event handler
 */
export function delegateEvent(parent, selector, eventType, handler) {
  if (!parent) return;
  parent.addEventListener(eventType, (e) => {
    const target = e.target.closest(selector);
    if (target) handler(e, target);
  });
}

/**
 * Batch DOM updates using DocumentFragment
 * @param {Array<HTMLElement>} elements - Elements to append
 * @returns {DocumentFragment} Fragment containing all elements
 */
export function createFragment(elements) {
  const fragment = document.createDocumentFragment();
  elements.forEach(el => fragment.appendChild(el));
  return fragment;
}

/**
 * Smooth scroll to element
 * @param {HTMLElement} element - Element to scroll to
 * @param {number} offset - Offset from top
 */
export function scrollToElement(element, offset = 0) {
  if (!element) return;
  window.scrollTo({
    top: element.offsetTop - offset,
    behavior: 'smooth'
  });
}

/**
 * Get element's offset from top of page
 * @param {HTMLElement} element - Element to measure
 * @returns {number} Offset in pixels
 */
export function getOffsetTop(element) {
  if (!element) return 0;
  return element.offsetTop;
}

/**
 * Cache multiple DOM elements
 * @param {Object} selectors - Object with keys and selector values
 * @returns {Object} Object with keys and element values
 */
export function cacheElements(selectors) {
  const cached = {};
  for (const [key, selector] of Object.entries(selectors)) {
    if (selector.startsWith('#')) {
      cached[key] = document.getElementById(selector.slice(1));
    } else if (selector.startsWith('.')) {
      cached[key] = document.querySelector(selector);
    } else {
      cached[key] = document.querySelector(selector);
    }
  }
  return cached;
}