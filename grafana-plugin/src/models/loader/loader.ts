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
    if (typeof actionKey === 'string') {
      this.items[actionKey] = isLoading;
    } else {
      actionKey.forEach((key) => {
        this.items[key] = isLoading;
      });
    }
  }
}

export const LoaderStore = new LoaderStoreClass();
