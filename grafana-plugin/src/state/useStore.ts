import React from 'react';

import { MobXProviderContext } from 'mobx-react';

import { RootStore } from './index';

export function useStore(): RootStore {
  const { store } = React.useContext(MobXProviderContext);

  return store;
}
