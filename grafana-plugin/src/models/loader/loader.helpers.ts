import { LoaderStore } from './loader';

export class LoaderHelper {
  static isLoading(store: typeof LoaderStore, actionKey: string | string[]) {
    return typeof actionKey === 'string' ? store.items[actionKey] : actionKey.some((key) => store.items[key]);
  }
}
