import React from 'react';

import { MobXProviderContext } from 'mobx-react';

import { RootStore } from './index';

export const useStore = (): RootStore => React.useContext(MobXProviderContext).store;
