import React from 'react';

import { NavigateFunction, useLocation, useNavigate, useParams } from 'react-router-dom-v5-compat';

import { useDrawer } from './hooks';

export const withDrawer = <T extends string>(Component: React.ComponentType<any>) => {
  const ComponentWithDrawer = (props: any) => {
    const drawerConfig = useDrawer<T>();
    return <Component {...props} drawerConfig={drawerConfig} />;
  };
  return ComponentWithDrawer;
};

interface Router<T> {
  location: Location;
  navigate: NavigateFunction;
  params: Readonly<T>;
}

export interface PropsWithRouter<T> {
  router: Router<T>;
}

export function withRouter<X, T extends PropsWithRouter<X>>(Component: React.FC<T>): React.FC<Omit<T, 'router'>> {
  function HOCWithRouter(props: T) {
    const location = useLocation();
    const navigate = useNavigate();
    const params = useParams() as unknown as X;

    return <Component {...props} router={{ location, navigate, params }} />;
  }

  return HOCWithRouter;
}
