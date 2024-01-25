import React from 'react';

import { Drawer } from '@grafana/ui';
import { observer } from 'mobx-react';

import { DrawerKeyToContentMap, DrawerKeyToTitleMap } from 'models/drawer/drawer.types';
import { useStore } from 'state/useStore';

const GlobalDrawer = observer(() => {
  const {
    drawerStore: { openedDrawerKey, closeDrawer },
  } = useStore();

  const Component = DrawerKeyToContentMap[openedDrawerKey];

  return DrawerKeyToTitleMap[openedDrawerKey] ? (
    <Drawer title={DrawerKeyToTitleMap[openedDrawerKey]} onClose={closeDrawer} closeOnMaskClick={false}>
      <Component />
    </Drawer>
  ) : null;
});

export default GlobalDrawer;
