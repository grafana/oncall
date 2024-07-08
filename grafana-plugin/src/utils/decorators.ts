import { LoaderStore } from 'models/loader/loader';
import { openErrorNotification, openNotification, openWarningNotification } from 'utils/utils';

export function AutoLoadingState(actionKey: string) {
  return function (_target: object, _key: string, descriptor: PropertyDescriptor) {
    let nbOfPendingActions = 0;
    const originalFunction = descriptor.value;
    descriptor.value = async function (...args: any) {
      LoaderStore.setLoadingAction(actionKey, true);
      nbOfPendingActions++;
      try {
        return await originalFunction.apply(this, args);
      } finally {
        nbOfPendingActions--;
        // if there are other pending actions with the same key, wait till the last one is done
        if (nbOfPendingActions === 0) {
          LoaderStore.setLoadingAction(actionKey, false);
        }
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
  composeFailureMessageFn?: (error: Response) => Promise<string>;
  failureType?: 'error' | 'warning';
};

export function WrapWithGlobalNotification(
  callback: Function,
  { success, failure, composeFailureMessageFn, failureType = 'error' }: GlobalNotificationConfig
) {
  return async (...params) => {
    try {
      await callback(...params);
      success && openNotification(success);
    } catch (err) {
      const open = failureType === 'error' ? openErrorNotification : openWarningNotification;
      const message = composeFailureMessageFn ? await composeFailureMessageFn(err) : failure;
      open(message);
      throw err;
    }
  };
}

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
        success && openNotification(success);
        return response;
      } catch (err) {
        const open = failureType === 'error' ? openErrorNotification : openWarningNotification;
        const message = composeFailureMessageFn ? await composeFailureMessageFn(err) : failure;
        open(message);
        throw err;
      }
    };
  };
}
