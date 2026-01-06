import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Custom hook for keyboard navigation
 * Provides Tab navigation, Enter/Escape shortcuts, and focus management
 */
export function useKeyboardNavigation({
  onEnter,
  onEscape,
  onArrowUp,
  onArrowDown,
  enabled = true,
}) {
  const handleKeyDown = useCallback(
    (event) => {
      if (!enabled) return;

      switch (event.key) {
        case 'Enter':
          if (onEnter && !event.shiftKey) {
            event.preventDefault();
            onEnter(event);
          }
          break;
        case 'Escape':
          if (onEscape) {
            event.preventDefault();
            onEscape(event);
          }
          break;
        case 'ArrowUp':
          if (onArrowUp) {
            event.preventDefault();
            onArrowUp(event);
          }
          break;
        case 'ArrowDown':
          if (onArrowDown) {
            event.preventDefault();
            onArrowDown(event);
          }
          break;
        default:
          break;
      }
    },
    [enabled, onEnter, onEscape, onArrowUp, onArrowDown]
  );

  useEffect(() => {
    if (enabled) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [enabled, handleKeyDown]);

  return { handleKeyDown };
}

/**
 * Hook for managing focus within a list of items
 */
export function useFocusNavigation(items, options = {}) {
  const {
    loop = true,
    orientation = 'vertical',
    onSelect,
    initialIndex = -1,
  } = options;

  const [focusedIndex, setFocusedIndex] = useState(initialIndex);
  const itemRefs = useRef([]);

  const focusItem = useCallback(
    (index) => {
      if (index >= 0 && index < items.length) {
        setFocusedIndex(index);
        itemRefs.current[index]?.focus();
      }
    },
    [items.length]
  );

  const focusNext = useCallback(() => {
    setFocusedIndex((prev) => {
      const next = prev + 1;
      if (next >= items.length) {
        return loop ? 0 : prev;
      }
      return next;
    });
  }, [items.length, loop]);

  const focusPrevious = useCallback(() => {
    setFocusedIndex((prev) => {
      const next = prev - 1;
      if (next < 0) {
        return loop ? items.length - 1 : prev;
      }
      return next;
    });
  }, [items.length, loop]);

  const focusFirst = useCallback(() => {
    focusItem(0);
  }, [focusItem]);

  const focusLast = useCallback(() => {
    focusItem(items.length - 1);
  }, [focusItem, items.length]);

  const handleKeyDown = useCallback(
    (event) => {
      const isVertical = orientation === 'vertical';
      const nextKey = isVertical ? 'ArrowDown' : 'ArrowRight';
      const prevKey = isVertical ? 'ArrowUp' : 'ArrowLeft';

      switch (event.key) {
        case nextKey:
          event.preventDefault();
          focusNext();
          break;
        case prevKey:
          event.preventDefault();
          focusPrevious();
          break;
        case 'Home':
          event.preventDefault();
          focusFirst();
          break;
        case 'End':
          event.preventDefault();
          focusLast();
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          if (focusedIndex >= 0 && onSelect) {
            onSelect(items[focusedIndex], focusedIndex);
          }
          break;
        default:
          break;
      }
    },
    [
      orientation,
      focusNext,
      focusPrevious,
      focusFirst,
      focusLast,
      focusedIndex,
      items,
      onSelect,
    ]
  );

  // Focus item when index changes
  useEffect(() => {
    if (focusedIndex >= 0 && focusedIndex < items.length) {
      itemRefs.current[focusedIndex]?.focus();
    }
  }, [focusedIndex, items.length]);

  const getItemProps = useCallback(
    (index) => ({
      ref: (el) => {
        itemRefs.current[index] = el;
      },
      tabIndex: focusedIndex === index ? 0 : -1,
      onKeyDown: handleKeyDown,
      onFocus: () => setFocusedIndex(index),
      'aria-selected': focusedIndex === index,
    }),
    [focusedIndex, handleKeyDown]
  );

  return {
    focusedIndex,
    setFocusedIndex,
    focusItem,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    getItemProps,
    handleKeyDown,
  };
}

/**
 * Hook for focus trap within a container (useful for modals)
 */
export function useFocusTrap(containerRef, options = {}) {
  const { enabled = true, autoFocus = true, restoreFocus = true } = options;
  const previousActiveElement = useRef(null);

  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    // Store previously focused element
    previousActiveElement.current = document.activeElement;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Auto focus first element
    if (autoFocus && firstElement) {
      firstElement.focus();
    }

    const handleKeyDown = (event) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);

      // Restore focus
      if (restoreFocus && previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [enabled, containerRef, autoFocus, restoreFocus]);
}

/**
 * Hook for skip links (accessibility navigation)
 */
export function useSkipLink(targetId) {
  const handleClick = useCallback(
    (event) => {
      event.preventDefault();
      const target = document.getElementById(targetId);
      if (target) {
        target.focus();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    },
    [targetId]
  );

  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        handleClick(event);
      }
    },
    [handleClick]
  );

  return { onClick: handleClick, onKeyDown: handleKeyDown };
}

/**
 * Hook for managing live region announcements
 */
export function useLiveAnnouncer() {
  const [announcement, setAnnouncement] = useState('');
  const [politeness, setPoliteness] = useState('polite');

  const announce = useCallback((message, level = 'polite') => {
    setPoliteness(level);
    // Clear first to ensure screen readers pick up repeated messages
    setAnnouncement('');
    setTimeout(() => setAnnouncement(message), 100);
  }, []);

  const clear = useCallback(() => {
    setAnnouncement('');
  }, []);

  const LiveRegion = useCallback(
    () => (
      <div
        role="status"
        aria-live={politeness}
        aria-atomic="true"
        className="sr-only"
      >
        {announcement}
      </div>
    ),
    [announcement, politeness]
  );

  return { announce, clear, LiveRegion };
}

/**
 * Utility function to generate unique IDs for accessibility
 */
let idCounter = 0;
export function useId(prefix = 'id') {
  const [id] = useState(() => `${prefix}-${++idCounter}`);
  return id;
}

/**
 * Hook for managing ARIA attributes
 */
export function useAriaAttributes(props) {
  const {
    isExpanded,
    isSelected,
    isDisabled,
    isRequired,
    hasError,
    errorMessage,
    describedBy,
    labelledBy,
    controls,
  } = props;

  return {
    'aria-expanded': isExpanded,
    'aria-selected': isSelected,
    'aria-disabled': isDisabled,
    'aria-required': isRequired,
    'aria-invalid': hasError,
    'aria-errormessage': errorMessage,
    'aria-describedby': describedBy,
    'aria-labelledby': labelledBy,
    'aria-controls': controls,
  };
}

export default useKeyboardNavigation;
