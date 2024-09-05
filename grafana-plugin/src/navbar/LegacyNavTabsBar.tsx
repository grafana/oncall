import React from 'react';

import { css } from '@emotion/css';
import { IconName, Tab, TabsBar } from '@grafana/ui';

import { pages } from 'pages/pages';
import { useStore } from 'state/useStore';

export const LegacyNavTabsBar = function ({ currentPage }: { currentPage: string }): JSX.Element {
  const store = useStore();

  const navigationPages = Object.keys(pages)
    .map((page) => pages[page])
    .filter((page) => (page.hideFromTabsFn ? !page.hideFromTabsFn(store) : !page.hideFromTabs));

  return (
    <div
      className={css`
        overflow-x: auto;
        white-space: nowrap;
      `}
    >
      <TabsBar>
        {navigationPages.map((page, index) => (
          <Tab
            key={index}
            icon={page.icon as IconName}
            label={page.text}
            href={page.path}
            active={
              currentPage === page.id ||
              (currentPage === 'schedule' && page.id === 'schedules') ||
              (currentPage === 'incident' && page.id === 'incidents')
            }
          />
        ))}
      </TabsBar>
    </div>
  );
};
