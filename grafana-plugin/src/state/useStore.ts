import React from 'react';

import { MobXProviderContext } from 'mobx-react';

import { RootStore } from './rootStore';

export function useStore(): RootStore {
  const { store } = React.useContext(MobXProviderContext);
  return store;
}
