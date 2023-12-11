import { LoaderStore } from 'models/loader/loader';
import { openErrorNotification, openNotification, openWarningNotification } from 'utils';

export function AutoLoadingState(actionKey: string) {
  return function (_target: object, _key: string, descriptor: PropertyDescriptor) {
    const originalFunction = descriptor.value;
    descriptor.value = async function (...args: any) {
      LoaderStore.setLoadingAction(actionKey, true);
      try {
        await originalFunction.apply(this, args);
      } finally {
        LoaderStore.setLoadingAction(actionKey, false);
      }
    };
  };
}

export function WrapAutoLoadingState(callback: Function, actionKey: string): (...params: any[]) => Promise<void> {
  return async (...params) => {
    LoaderStore.setLoadingAction(actionKey, true);

    try {
      await callback(...params);
    } finally {
      LoaderStore.setLoadingAction(actionKey, false);
    }
  };
}

type GlobalNotificationConfig = {
  success?: string;
  failure?: string;
  composeFailureMessageFn?: (error: unknown) => string;
  failureType?: 'error' | 'warning';
};

export function WithGlobalNotification({
  success,
  failure,
  composeFailureMessageFn,
  failureType = 'error',
}: GlobalNotificationConfig) {
  return function (_target: object, _key: string, descriptor: PropertyDescriptor) {
    const childFunction = descriptor.value;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    descriptor.value = async function (...args: any) {
      try {
        const response = await childFunction.apply(this, args);
        openNotification(success);
        return response;
      } catch (err) {
        const open = failureType === 'error' ? openErrorNotification : openWarningNotification;
        const message = composeFailureMessageFn ? composeFailureMessageFn(err) : failure;
        open(message);
        throw err;
      }
    };
  };
}
