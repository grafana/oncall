import { useEffect, useRef, useState } from 'react';
import { useMemo } from 'react';

import { AppRootProps, NavModelItem } from '@grafana/data';

import { PageDefinition } from 'pages';

import { APP_TITLE, APP_SUBTITLE } from './consts';

type Args = {
  meta: AppRootProps['meta'];
  pages: PageDefinition[];
  path: string;
  page: string;
  grafanaUser: {
    orgRole: 'Viewer' | 'Editor' | 'Admin';
  };
  enableLiveSettings: boolean;
};

export function useForceUpdate() {
  const [value, setValue] = useState(0);
  return () => setValue((value) => value + 1);
}

export function useNavModel({ meta, pages, path, page, grafanaUser, enableLiveSettings }: Args) {
  return useMemo(() => {
    const tabs: NavModelItem[] = [];

    pages.forEach(({ text, icon, id, role, hideFromTabs }) => {
      tabs.push({
        text,
        icon,
        id,
        url: `${path}?page=${id}`,
        hideFromTabs:
          hideFromTabs ||
          (role === 'Admin' && grafanaUser.orgRole !== role) ||
          (id === 'live-settings' && !enableLiveSettings),
      });

      if (page === id) {
        tabs[tabs.length - 1].active = true;
      }
    });

    // Fallback if current `tab` doesn't match any page
    if (!tabs.some(({ active }) => active)) {
      tabs[0].active = true;
    }

    const node = {
      text: APP_TITLE,
      img: meta.info.logos.large,
      subTitle: APP_SUBTITLE,
      url: path,
      children: tabs,
    };

    return {
      node,
      main: node,
    };
  }, [meta.info.logos.large, pages, path, page, enableLiveSettings]);
}

export function usePrevious(value: any) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
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
