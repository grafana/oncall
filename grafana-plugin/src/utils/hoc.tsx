import React from 'react';

import { useDrawer } from './hooks';

export const withDrawer = <T extends string>(Component: React.ComponentType<any>) => {
  const ComponentWithDrawer = (props: any) => {
    const drawerConfig = useDrawer<T>();
    return <Component {...props} drawerConfig={drawerConfig} />;
  };
  return ComponentWithDrawer;
};
