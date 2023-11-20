import { LoaderStore } from 'models/loader/loader';

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
