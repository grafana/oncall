import React, { useEffect, useRef, useState, useMemo } from 'react';

import { AppRootProps, NavModelItem } from '@grafana/data';
import { useLocation } from 'react-router-dom';

import NavBarSubtitle from 'components/NavBar/NavBarSubtitle';
import { NavMenuItem } from 'components/PluginLink/routes';
import { PageDefinition } from 'pages/routes';

import { APP_TITLE } from './consts';

export function useForceUpdate() {
  const [, setValue] = useState(0);
  return () => setValue((value) => value + 1);
}

export function usePrevious(value: any) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

export function useQueryParams() {
  const { search } = useLocation();

  return React.useMemo(() => new URLSearchParams(search), [search]);
}

export function useQueryPath() {
  const location = useLocation();
  return React.useMemo(() => location.pathname, [location]);
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
