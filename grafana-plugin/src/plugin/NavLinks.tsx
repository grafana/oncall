import React from 'react';

import { Tab, TabsBar } from '@grafana/ui';
import { pages } from 'pages';
import { IconName } from '@grafana/data';

export default function NavLinks({ currentPage }: { currentPage: string }): JSX.Element {
  const navigationPages = Object.keys(pages)
    .map((page) => pages[page])
    .filter((page) => !page.hideFromTabs);

  return (
    <TabsBar>
      {navigationPages.map((page) => (
        <Tab icon={page.icon as IconName} label={page.text} href={page.path} active={currentPage === page.id} />
      ))}
    </TabsBar>
  );
}
