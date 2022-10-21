import React, { useEffect, useRef, useState, useMemo } from 'react';

import { AppRootProps, NavModelItem } from '@grafana/data';

import NavBarSubtitle from 'components/NavBar/NavBarSubtitle';
import { PageDefinition } from 'pages';
import { RootBaseStore } from 'state/rootBaseStore';

import { APP_TITLE } from './consts';

type Args = {
  meta: AppRootProps['meta'];
  pages: PageDefinition[];
  path: string;
  page: string;
  store: RootBaseStore;
  enableLiveSettings: boolean;
  enableCloudPage: boolean;
  enableNewSchedulesPage: boolean;
  backendLicense: string;
};

export function useForceUpdate() {
  const [, setValue] = useState(0);
  return () => setValue((value) => value + 1);
}

export function useNavModel({
  meta,
  pages,
  path,
  page,
  store,
  enableLiveSettings,
  enableCloudPage,
  enableNewSchedulesPage,
  backendLicense,
}: Args) {
  return useMemo(() => {
    const tabs: NavModelItem[] = [];

    pages.forEach(({ text, icon, id, action, hideFromTabs }) => {
      tabs.push({
        text,
        icon,
        id,
        url: `${path}?page=${id}`,
        hideFromTabs:
          hideFromTabs ||
          (action && !store.isUserActionAllowed(action)) ||
          (id === 'live-settings' && !enableLiveSettings) ||
          (id === 'cloud' && !enableCloudPage) ||
          (id === 'schedules-new' && !enableNewSchedulesPage),
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
      subTitle: <NavBarSubtitle backendLicense={backendLicense} />,
      url: path,
      children: tabs,
    };

    return {
      node,
      main: node,
    };
  }, [
    meta.info.logos.large,
    pages,
    path,
    page,
    enableLiveSettings,
    enableCloudPage,
    backendLicense,
    enableNewSchedulesPage,
  ]);
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
