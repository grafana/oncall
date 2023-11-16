import { observable } from 'mobx';

interface LoadingResult {
  [key: string]: boolean;
}

class LoaderStore {
  @observable
  items: LoadingResult = {};

  setLoadingAction(actionKey: string, isLoading: boolean) {
    this.items[actionKey] = isLoading;
  }

  isLoading(actionKey: string): boolean {
    return !!this.items[actionKey];
  }
}

export default new LoaderStore() as LoaderStore;
