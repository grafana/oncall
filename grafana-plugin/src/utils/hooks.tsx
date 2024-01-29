import React, { useEffect, useRef, useState } from 'react';

import { useLocation } from 'react-router-dom';

import LocationHelper from './LocationHelper';

export function useForceUpdate() {
  const [, setValue] = useState(0);
  return () => setValue((value) => value + 1);
}

export function useOnClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }

      handler(event);
    };
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}

export function usePrevious(value: any) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

export function useQueryParams(): URLSearchParams {
  const { search } = useLocation();

  return React.useMemo(() => new URLSearchParams(search), [search]);
}

export function useDebouncedCallback<A extends any[]>(callback: (...args: A) => void, wait: number) {
  // track args & timeout handle between calls
  const argsRef = useRef<A>();
  const timeout = useRef<ReturnType<typeof setTimeout>>();

  function cleanup() {
    if (timeout.current) {
      clearTimeout(timeout.current);
    }
  }

  // make sure our timeout gets cleared if
  // our consuming component gets unmounted
  useEffect(() => cleanup, []);

  return function debouncedCallback(...args: A) {
    // capture latest args
    argsRef.current = args;

    // clear debounce timer
    cleanup();

    // start waiting again
    timeout.current = setTimeout(() => {
      if (argsRef.current) {
        callback(...argsRef.current);
      }
    }, wait);
  };
}

export const useDrawerState = <DrawerKey extends string, DrawerData = unknown>(initialDrawerData?: DrawerData) => {
  const [openedDrawer, setOpenedDrawer] = useState<DrawerKey>(LocationHelper.getQueryParam('openedDrawerKey'));
  const [drawerData, setDrawerData] = useState<DrawerData>(initialDrawerData);

  return {
    openDrawer: (drawerKey: DrawerKey, drawerData?: DrawerData) => {
      setOpenedDrawer(drawerKey);
      if (drawerData) {
        setDrawerData(drawerData);
      }
      LocationHelper.update({ openedDrawerKey: drawerKey }, 'partial');
    },
    closeDrawer: () => {
      setOpenedDrawer(undefined);
      LocationHelper.update({ openedDrawerKey: undefined }, 'partial');
    },
    getIsDrawerOpened: (drawerKey: DrawerKey) => openedDrawer === drawerKey,
    openedDrawer,
    drawerData,
  };
};
