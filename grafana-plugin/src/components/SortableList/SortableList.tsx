import React from 'react';

import { SortableContainer, SortableContainerProps } from 'react-sortable-hoc';

import { Timeline } from 'components/Timeline/Timeline';

export const SortableList = SortableContainer<
  SortableContainerProps & { className?: string; children: React.ReactNode[] }
>(({ className, children }: any) => {
  return <Timeline className={className}>{children}</Timeline>;
});
