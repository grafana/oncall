export const waitForElement = (selector: string) => {
  return new Promise((resolve) => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }

    const observer = new MutationObserver((_mutations) => {
      if (document.querySelector(selector)) {
        resolve(document.querySelector(selector));
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
};

export const scrollToElement = (element: Element, behavior: ScrollBehavior = 'instant' as ScrollBehavior) => {
  element.scrollIntoView({ behavior, block: 'center' });
};

export const getCoords = (elem) => {
  // crossbrowser version
  const box = elem.getBoundingClientRect();

  const body = document.body;
  const docEl = document.documentElement;

  const scrollTop = window.scrollY || docEl.scrollTop || body.scrollTop;
  const scrollLeft = window.scrollX || docEl.scrollLeft || body.scrollLeft;

  const clientTop = docEl.clientTop || body.clientTop || 0;
  const clientLeft = docEl.clientLeft || body.clientLeft || 0;

  const top = box.top + scrollTop - clientTop;
  const left = box.left + scrollLeft - clientLeft;

  return { top: Math.round(top), left: Math.round(left) };
};

export const HTML_ID = {
  SCHEDULE_FINAL: 'oncall-schedule-final',
  SCHEDULE_ROTATIONS: 'oncall-schedule-rotations',
  SCHEDULE_OVERRIDES_AND_SWAPS: 'oncall-schedule-overrides-and-swaps',
} as const;
