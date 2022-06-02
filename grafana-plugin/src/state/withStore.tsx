import React from 'react';

import { MobXProviderContext } from 'mobx-react';

export const withMobXProviderContext = (BaseComponent: any) => (props: any) => {
  return (
    <MobXProviderContext.Consumer>
      {(mobXProviderContext) => <BaseComponent {...props} store={mobXProviderContext.store} />}
    </MobXProviderContext.Consumer>
  );
};
