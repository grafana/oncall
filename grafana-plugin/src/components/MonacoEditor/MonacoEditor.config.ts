// Mostly used for input fields where we're hiding scrollbars
export const MONACO_READONLY_CONFIG = {
  renderLineHighlight: false,
  readOnly: true,
  scrollbar: {
    vertical: 'hidden',
    horizontal: 'hidden',
    verticalScrollbarSize: 0,
    handleMouseWheel: false,
  },
  hideCursorInOverviewRuler: true,
  minimap: { enabled: false },
  cursorStyle: {
    display: 'none',
  },
};

export const MONACO_EDITABLE_CONFIG = {
  renderLineHighlight: false,
  readOnly: false,
  hideCursorInOverviewRuler: true,
  minimap: { enabled: false },
  cursorStyle: {
    display: 'none',
  },
};
