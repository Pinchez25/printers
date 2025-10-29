export function initAnimations() {
  const target = document.querySelector('.hero-title .text-gradient');
  if (!target || target.dataset.typewriterInitialized === 'true') return;

  target.dataset.typewriterInitialized = 'true';

  const FINAL_TEXT = 'Peashan Brands';
  const phrases = ['Premium Branding', 'Printing Solutions', 'Design That Delivers', FINAL_TEXT];
  const typeSpeed = 55;
  const backSpeed = 32;
  const backDelay = 900;
  const startDelay = 300;

  target.setAttribute('aria-live', 'polite');

  const textNode = document.createTextNode('');
  const caret = document.createElement('span');
  caret.className = 'typing-caret';

  const safeSetText = (text) => textNode.nodeValue = text;

  setTimeout(() => {
    while (target.firstChild) target.removeChild(target.firstChild);
    target.appendChild(textNode);
    target.appendChild(caret);
    runSequence(0);
  }, startDelay);

  function typeNextChar(str, index, onDone) {
    if (index < str.length) {
      safeSetText(str.slice(0, index + 1));
      setTimeout(() => typeNextChar(str, index + 1, onDone), typeSpeed);
    } else {
      onDone?.();
    }
  }

  function backspacePrevChar(current, onDone) {
    if (current.length > 0) {
      safeSetText(current.slice(0, -1));
      setTimeout(() => backspacePrevChar(textNode.nodeValue, onDone), backSpeed);
    } else {
      onDone?.();
    }
  }

  function runSequence(phraseIdx) {
    const str = phrases[phraseIdx];
    const currentLen = (textNode.nodeValue || '').length;
    typeNextChar(str, currentLen, () => {
      if (str === FINAL_TEXT) {
        finish();
        return;
      }
      setTimeout(() => {
        backspacePrevChar(textNode.nodeValue, () => runSequence(phraseIdx + 1));
      }, backDelay);
    });
  }

  function finish() {
    safeSetText(FINAL_TEXT);
    setTimeout(() => {
      if (caret?.parentNode) caret.parentNode.removeChild(caret);
    }, 350);
    target.removeAttribute('aria-live');
  }
}