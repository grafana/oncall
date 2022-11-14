import React from 'react';

import { IconName } from '@grafana/data';
import { Tab, TabsBar } from '@grafana/ui';

import { pages } from 'pages';
import { useStore } from 'state/useStore';

export default function NavLinks({ currentPage }: { currentPage: string }): JSX.Element {
  const store = useStore();

  const navigationPages = Object.keys(pages)
    .map((page) => pages[page])
    .filter((page) => {
      if (page.hideFromTabsFn) {
        return page.hideFromTabsFn(store);
      }
      return !page.hideFromTabs;
    });

  return (
    <TabsBar>
      {navigationPages.map((page, index) => (
        <Tab
          key={index}
          icon={page.icon as IconName}
          label={page.text}
          href={page.path}
          active={currentPage === page.id}
        />
      ))}
    </TabsBar>
  );
}
