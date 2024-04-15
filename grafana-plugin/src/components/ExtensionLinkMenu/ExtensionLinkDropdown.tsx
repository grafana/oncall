import React, { ReactElement, useMemo, useState } from 'react';

import { PluginExtensionLink } from '@grafana/data';
import { getPluginLinkExtensions } from '@grafana/runtime';
import { Dropdown, ToolbarButton } from '@grafana/ui';
import { OnCallPluginExtensionPoints } from 'types';

import { ApiSchemas } from 'network/oncall-api/api.types';

import { ExtensionLinkMenu } from './ExtensionLinkMenu';

interface Props {
  alertGroup: ApiSchemas['AlertGroup'];
  extensionPointId: OnCallPluginExtensionPoints;
}

export function ExtensionLinkDropdown({ alertGroup, extensionPointId }: Props): ReactElement | null {
  const [isOpen, setIsOpen] = useState(false);
  const context = useExtensionPointContext(alertGroup);
  const extensions = useExtensionLinks(context, extensionPointId);

  if (extensions.length === 0) {
    return null;
  }

  const menu = <ExtensionLinkMenu alertGroup={alertGroup} extensions={extensions} />;

  return (
    <Dropdown onVisibleChange={setIsOpen} placement="bottom-start" overlay={menu}>
      <ToolbarButton aria-label="Actions" variant="canvas" isOpen={isOpen}>
        Actions
      </ToolbarButton>
    </Dropdown>
  );
}

function useExtensionPointContext(incident: ApiSchemas['AlertGroup']): PluginExtensionOnCallAlertGroupContext {
  return { alertGroup: incident };
}

function useExtensionLinks<T extends object>(
  context: T,
  extensionPointId: OnCallPluginExtensionPoints
): PluginExtensionLink[] {
  return useMemo(() => {
    // getPluginLinkExtensions is available in Grafana>=10.0,
    // so will be undefined in earlier versions. Just return an
    // empty list of extensions in this case.
    if (getPluginLinkExtensions === undefined) {
      return [];
    }
    const { extensions } = getPluginLinkExtensions({
      extensionPointId,
      context,
      limitPerPlugin: 3,
    });

    return extensions;
  }, [context]);
}

// This is the 'context' that will be passed to plugin extensions when they
// are created (in `getPluginLinkExtensions`, provided by Grafana).
//
// Other plugins should be able to use this context type in the `configure`
// or `onClick` handler of their extension.
interface PluginExtensionOnCallAlertGroupContext {
  alertGroup: ApiSchemas['AlertGroup'];
}
