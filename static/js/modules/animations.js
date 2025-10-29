export function initAnimations() {
  const target = document.querySelector('.hero-title .text-gradient');
  if (!target || target.dataset.typewriterInitialised === 'true') return;

  target.dataset.typewriterInitialised = 'true';

  const FINAL_TEXT = 'Peashan Brands';
  const phrases = ['Premium Branding', 'Printing Solutions', 'Design That Delivers', FINAL_TEXT];
  const typeSpeed = 45; 
  const backSpeed = 25; 
  const backDelay = 800; 
  const startDelay = 300;

  const timeouts = new Set();
  let isCleanedUp = false;

  const cleanup = () => {
    if (isCleanedUp) return;
    isCleanedUp = true;
    timeouts.forEach(id => clearTimeout(id));
    timeouts.clear();
    observer?.disconnect();
    target.dataset.typewriterInitialised = 'false';
  };

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.removedNodes) {
        if (node === target || node.contains(target)) {
          cleanup();
          return;
        }
      }
    }
  });

  observer.observe(target.parentNode, { childList: true, subtree: true });

  const safeTimeout = (fn, delay) => {
    if (isCleanedUp) return;
    const id = setTimeout(() => {
      timeouts.delete(id);
      if (!isCleanedUp) fn();
    }, delay);
    timeouts.add(id);
    return id;
  };

  target.setAttribute('aria-live', 'polite');

  const textNode = document.createTextNode('');
  const caret = document.createElement('span');
  caret.className = 'typing-caret';

  const safeSetText = (text) => {
    if (!isCleanedUp) textNode.nodeValue = text;
  };

  safeTimeout(() => {
    while (target.firstChild) target.removeChild(target.firstChild);
    target.appendChild(textNode);
    target.appendChild(caret);
    runSequence(0);
  }, startDelay);

  function typeNextChar(str, index, onDone) {
    if (isCleanedUp || index >= str.length) {
      if (!isCleanedUp && index >= str.length) onDone?.();
      return;
    }
    safeSetText(str.slice(0, index + 1));
    const speed = typeSpeed + (Math.random() - 0.5) * 20;
    safeTimeout(() => typeNextChar(str, index + 1, onDone), speed);
  }

  function backspacePrevChar(current, onDone) {
    if (isCleanedUp || current.length === 0) {
      if (!isCleanedUp && current.length === 0) onDone?.();
      return;
    }
    safeSetText(current.slice(0, -1));
    const speed = backSpeed + (Math.random() - 0.5) * 10;
    safeTimeout(() => backspacePrevChar(textNode.nodeValue, onDone), speed);
  }

  function runSequence(phraseIdx) {
    if (isCleanedUp) return;
    const str = phrases[phraseIdx];
    const currentLen = (textNode.nodeValue || '').length;
    typeNextChar(str, currentLen, () => {
      if (str === FINAL_TEXT) {
        finish();
        return;
      }
      safeTimeout(() => {
        backspacePrevChar(textNode.nodeValue, () => runSequence(phraseIdx + 1));
      }, backDelay);
    });
  }

  function finish() {
    safeSetText(FINAL_TEXT);
    safeTimeout(() => {
      if (caret?.parentNode) caret.parentNode.removeChild(caret);
      cleanup();
    }, 350);
    target.removeAttribute('aria-live');
  }

  return cleanup;
}
