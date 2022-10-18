import React, { useEffect, useRef, useState, useMemo } from 'react';

import { AppRootProps, NavModelItem } from '@grafana/data';

import NavBarSubtitle from 'components/NavBar/NavBarSubtitle';
import { PageDefinition } from 'pages';
import { useLocation } from 'react-router-dom';

import { APP_TITLE } from './consts';

type Args = {
  meta: AppRootProps['meta'];
  pages: PageDefinition[];
  path: string;
  page: string;
  grafanaUser: {
    orgRole: 'Viewer' | 'Editor' | 'Admin';
  };
  enableLiveSettings: boolean;
  enableCloudPage: boolean;
  enableNewSchedulesPage: boolean;
  backendLicense: string;
  onNavChanged: any;
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
  grafanaUser,
  enableLiveSettings,
  enableCloudPage,
  enableNewSchedulesPage,
  backendLicense,
  onNavChanged
}: Args) {
  const location = useLocation();

  useEffect(() => {
    let hasActivePage = false;
    const tabs = pages.map(({ text, icon, path, role, hideFromTabs, id }) => {
      hasActivePage = hasActivePage || page === id;
      return {
        text: text,
        icon: icon,
        id: id,
        url: path,
        active: page === id,
        hideFromTabs:
          hideFromTabs ||
          (role === 'Admin' && grafanaUser.orgRole !== role) ||
          (id === 'live-settings' && !enableLiveSettings) ||
          (id === 'cloud' && !enableCloudPage) ||
          (id === 'schedules-new' && !enableNewSchedulesPage),
      };
    });

    if (!hasActivePage) {
      tabs[0].active = true;
    }

    const node = {
      text: APP_TITLE,
      img: meta.info.logos.large,
      subTitle: <NavBarSubtitle backendLicense={backendLicense} />,
      url: path,
      children: tabs,
    };

    const navModel = {
      node,
      main: node,
    };

    onNavChanged(navModel)
  }, [
    meta.info.logos.large,
    pages,
    path,
    page,
    location,
    enableLiveSettings,
    enableCloudPage,
    backendLicense,
    enableNewSchedulesPage,
    grafanaUser.orgRole,
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
