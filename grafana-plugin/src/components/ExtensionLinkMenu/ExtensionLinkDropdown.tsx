import React, { ReactElement, useMemo, useState } from 'react';

import { PluginExtensionLink } from '@grafana/data';
import {
  type GetPluginExtensionsOptions,
  getPluginLinkExtensions,
  usePluginLinks as originalUsePluginLinks,
} from '@grafana/runtime';
import { Dropdown, ToolbarButton } from '@grafana/ui';
import { OnCallPluginExtensionPoints } from 'types';

import { ApiSchemas } from 'network/oncall-api/api.types';

import { ExtensionLinkMenu } from './ExtensionLinkMenu';

interface Props {
  incident: ApiSchemas['AlertGroup'];
  extensionPointId: OnCallPluginExtensionPoints;
  declareIncidentLink?: string;
  grafanaIncidentId: string | null;
}

// `usePluginLinks()` is only available in Grafana>=11.1.0, so we have a fallback for older versions
const usePluginLinks = originalUsePluginLinks === undefined ? usePluginLinksFallback : originalUsePluginLinks;

export function ExtensionLinkDropdown({
  incident,
  extensionPointId,
  declareIncidentLink,
  grafanaIncidentId,
}: Props): ReactElement | null {
  const [isOpen, setIsOpen] = useState(false);
  const context = useExtensionPointContext(incident);
  const { links, isLoading } = usePluginLinks({ context, extensionPointId, limitPerPlugin: 3 });

  if (links.length === 0 || isLoading) {
    return null;
  }

  const menu = (
    <ExtensionLinkMenu
      extensions={links}
      declareIncidentLink={declareIncidentLink}
      grafanaIncidentId={grafanaIncidentId}
    />
  );

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

function usePluginLinksFallback<T extends object>({
  context,
  extensionPointId,
  limitPerPlugin,
}: GetPluginExtensionsOptions): { links: PluginExtensionLink[]; isLoading: boolean } {
  return useMemo(() => {
    // getPluginLinkExtensions is available in Grafana>=10.0,
    // so will be undefined in earlier versions. Just return an
    // empty list of extensions in this case.
    if (getPluginLinkExtensions === undefined) {
      return {
        links: [],
        isLoading: false,
      };
    }

    const { extensions } = getPluginLinkExtensions({
      extensionPointId,
      context,
      limitPerPlugin,
    });

    return {
      links: extensions,
      isLoading: false,
    };
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
