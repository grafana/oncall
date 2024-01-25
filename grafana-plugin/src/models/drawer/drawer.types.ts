import { ComponentType } from 'react';

import OutgoingEventTriggerDrawerContent from 'containers/drawers/OutgoingEventTriggerDrawerContent';

export const DrawerKey = {
  OutgoingEventTrigger: 'OutgoingEventTrigger',
} as const;
export type DrawerKey = (typeof DrawerKey)[keyof typeof DrawerKey];

export const DrawerKeyToContentMap: Record<DrawerKey, ComponentType> = {
  OutgoingEventTrigger: OutgoingEventTriggerDrawerContent,
};

export const DrawerKeyToTitleMap: Record<DrawerKey, string> = {
  OutgoingEventTrigger: 'Trigger event details',
};
