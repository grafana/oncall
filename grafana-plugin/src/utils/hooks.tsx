import React, { ComponentProps, useEffect, useRef, useState } from 'react';

import { ConfirmModal, useStyles2 } from '@grafana/ui';
import { useLocation } from 'react-router-dom';

import { ActionKey } from 'models/loader/action-keys';
import { LoaderHelper } from 'models/loader/loader.helpers';
import { useStore } from 'state/useStore';

import { LocationHelper } from './LocationHelper';
import { getCommonStyles } from './styles';

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

export const useDrawer = <DrawerKey extends string, DrawerData = unknown>(initialDrawerData?: DrawerData) => {
  const [openedDrawerKey, setOpenedDrawerKey] = useState<DrawerKey>(LocationHelper.getQueryParam('openedDrawerKey'));
  const [drawerData, setDrawerData] = useState<DrawerData>(initialDrawerData);

  return {
    openDrawer: (drawerKey: DrawerKey, drawerData?: DrawerData) => {
      setOpenedDrawerKey(drawerKey);
      if (drawerData) {
        setDrawerData(drawerData);
      }
      LocationHelper.update({ openedDrawerKey: drawerKey }, 'partial');
    },
    closeDrawer: () => {
      setOpenedDrawerKey(undefined);
      LocationHelper.update({ openedDrawerKey: undefined }, 'partial');
    },
    getIsDrawerOpened: (drawerKey: DrawerKey) => openedDrawerKey === drawerKey,
    openedDrawerKey,
    drawerData,
  };
};

type ConfirmModalProps = ComponentProps<typeof ConfirmModal>;
export const useConfirmModal = () => {
  const [modalProps, setModalProps] = useState<ConfirmModalProps>();

  return {
    openModal: (modalProps: Pick<ConfirmModalProps, 'title' | 'onConfirm'> & Partial<ConfirmModalProps>) => {
      setModalProps({
        isOpen: true,
        confirmText: 'Confirm',
        dismissText: 'Cancel',
        onDismiss: () => setModalProps(undefined),
        body: null,
        ...modalProps,
        onConfirm: () => {
          modalProps.onConfirm();
          setModalProps(undefined);
        },
      });
    },
    closeModal: () => {
      setModalProps(undefined);
    },
    modalProps,
  };
};

export const useCommonStyles = () => useStyles2(getCommonStyles);

export const useIsLoading = (actionKey: ActionKey) => {
  const { loaderStore } = useStore();
  return LoaderHelper.isLoading(loaderStore, actionKey);
};

export const useOnMount = (callback: () => void) => {
  useEffect(() => {
    callback();
  }, []);
};
