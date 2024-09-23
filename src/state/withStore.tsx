import React from 'react';

import { MobXProviderContext } from 'mobx-react';

export const withMobXProviderContext = (BaseComponent: any) => {
  const MobXProviderWrappedComponent = (props: any) => (
    <MobXProviderContext.Consumer>
      {(mobXProviderContext) => <BaseComponent {...props} store={mobXProviderContext.store} />}
    </MobXProviderContext.Consumer>
  );

  return MobXProviderWrappedComponent;
};
