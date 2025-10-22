/**
 * Configuration constants for the application
 */
export const CONFIG = {
  PORTFOLIO: {
    ITEMS_PER_PAGE: 6,
    DESCRIPTION_MAX_LENGTH: 120,
    DEFAULT_DESCRIPTION: 'Premium printing project showcasing our quality work.',
    DEFAULT_IMAGE: '/static/default.jpg',
    API_ENDPOINT: '/api/gallery/'
  },
  ANIMATION: {
    SCROLL_THRESHOLD: 100,
    DEBOUNCE_DELAY: 300,
    THROTTLE_DELAY: 100,
    SEARCH_DEBOUNCE: 300
  },
  CAROUSEL: {
    AUTO_ADVANCE_INTERVAL: 4000
  },
  RESPONSIVE: {
    MOBILE_BREAKPOINT: 768,
    SMALL_MOBILE_BREAKPOINT: 480
  }
};