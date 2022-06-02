import React from 'react';

import { SortableContainer } from 'react-sortable-hoc';

import Timeline from 'components/Timeline/Timeline';

const SortableList = SortableContainer(({ className, children }: any) => {
  return <Timeline className={className}>{children}</Timeline>;
});

export default SortableList;
