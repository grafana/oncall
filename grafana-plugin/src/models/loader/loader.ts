import { action, observable, makeObservable } from 'mobx';

interface LoadingResult {
  [key: string]: boolean;
}

class LoaderStoreClass {
  @observable
  items: LoadingResult = {};

  constructor() {
    makeObservable(this);
  }

  @action.bound
  setLoadingAction(actionKey: string | string[], isLoading: boolean) {
    if (Array.isArray(actionKey)) {
      actionKey.forEach((key) => {
        this.items[key] = isLoading;
      });
    } else {
      this.items[actionKey] = isLoading;
    }
  }

  isLoading(actionKey: string): boolean {
    return !!this.items[actionKey];
  }
}

export const LoaderStore = new LoaderStoreClass();
