import { action, observable, makeObservable } from 'mobx';

import LocationHelper from 'utils/LocationHelper';

import { DrawerKey } from './drawer.types';

class DrawerStoreClass {
  @observable
  openedDrawerKey?: DrawerKey = LocationHelper.getQueryParams('openedDrawerKey');

  @observable
  drawerData?: unknown;

  constructor() {
    makeObservable(this);
  }

  @action
  openDrawer = ({ drawerKey, data }: { drawerKey: DrawerKey; data?: unknown }) => {
    if (data) {
      this.drawerData = data;
    }
    this.openedDrawerKey = drawerKey;
    LocationHelper.update({ openedDrawerKey: drawerKey }, 'partial');
  };

  @action
  closeDrawer = () => {
    this.openedDrawerKey = undefined;
    LocationHelper.update({ openedDrawerKey: undefined }, 'partial');
  };
}

export const DrawerStore = new DrawerStoreClass();
