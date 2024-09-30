import React, { ReactElement, useMemo } from 'react';

import { locationUtil, PluginExtensionLink, PluginExtensionTypes } from '@grafana/data';
import { IconName, Menu } from '@grafana/ui';
import { getPluginId, PLUGIN_ROOT } from 'helpers/consts';
import { truncateTitle } from 'helpers/string';

import { PluginBridge, SupportedPlugin } from 'components/PluginBridge/PluginBridge';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';

type Props = {
  webhookModal: {
    onOpenModal: () => void;
  };

  extensions: PluginExtensionLink[];
  // We require this to be passed in so we can continue to
  // create a custom Declare incident link. Once the Incident plugin
  // registers its own extension link, we can remove this.
  declareIncidentLink?: string;
  grafanaIncidentId?: string;
};

export function ExtensionLinkMenu({
  extensions,
  declareIncidentLink,
  grafanaIncidentId,
  webhookModal,
}: Props): ReactElement | null {
  const { categorised, uncategorised } = useExtensionLinksByCategory(extensions);
  const showDivider = uncategorised.length > 0 && Object.keys(categorised).length > 0;

  return (
    <Menu>
      <>
        <IRMActionSection
          webhookModal={webhookModal}
          extensions={extensions}
          declareIncidentLink={declareIncidentLink}
          grafanaIncidentId={grafanaIncidentId}
        />

        <RenderConditionally shouldRender={extensions.length > 0}>
          {Object.keys(categorised).map((category) => (
            <Menu.Group key={category} label={truncateTitle(category, 25)}>
              {renderItems(categorised[category])}
            </Menu.Group>
          ))}
          {showDivider && <Menu.Divider key="divider" />}
          {renderItems(uncategorised)}
        </RenderConditionally>
      </>
    </Menu>
  );
}

const IRMActionSection: React.FC<Props> = ({ webhookModal, extensions, declareIncidentLink, grafanaIncidentId }) => {
  return (
    <Menu.Group key={'IRM'} label={'IRM'}>
      <Menu.Item icon={'upload'} key={'triggerWebhook'} label={'Trigger webhook'} onClick={webhookModal.onOpenModal} />
      <RenderConditionally
        shouldRender={getPluginId() === 'grafana-irm-app'}
        backupChildren={
          <DeclareIncidentMenuItem
            extensions={extensions}
            declareIncidentLink={declareIncidentLink}
            grafanaIncidentId={grafanaIncidentId}
          />
        }
      >
        <Menu.Item
          label="Declare incident"
          icon="fire"
          // TODO: At some point we should update link on the backend so it points to IRM plugin and use it directly
          url={`${PLUGIN_ROOT}/incidents?declare=new&${declareIncidentLink.split('?')[1].replace('oncall', 'irm')}`}
        />
      </RenderConditionally>
    </Menu.Group>
  );
};

// This menu item is a temporary workaround for the fact that the Incident plugin doesn't
// register its own extension link.
// TODO: remove this once Incident is definitely registering its own extension link.
function DeclareIncidentMenuItem({
  extensions,
  declareIncidentLink,
  grafanaIncidentId,
}: Omit<Props, 'webhookModal'>): ReactElement | null {
  const declareIncidentExtensionLink = extensions.find(
    (extension) => extension.pluginId === 'grafana-incident-app' && extension.title === 'Declare incident'
  );

  if (
    // Don't show a custom Declare incident button if the Grafana Incident plugin already configured one.
    declareIncidentExtensionLink ||
    // Don't show a custom Declare incident button if there's no valid link.
    !declareIncidentLink ||
    // Don't show the button if an incident has already been declared from this alert group.
    grafanaIncidentId
  ) {
    return null;
  }

  return (
    <PluginBridge plugin={SupportedPlugin.Incident}>
      <>
        {renderItems([
          {
            type: PluginExtensionTypes.link,
            path: declareIncidentLink,
            icon: 'fire',
            category: 'Incident',
            title: 'Declare incident',
            pluginId: getPluginId(),
          } as Partial<PluginExtensionLink>,
        ])}
      </>
    </PluginBridge>
  );
}

function renderItems(extensions: Array<Partial<PluginExtensionLink>>): ReactElement[] {
  return extensions.map((extension) => (
    <Menu.Item
      ariaLabel={extension.title}
      icon={(extension?.icon || 'plug') as IconName}
      key={extension.id}
      label={truncateTitle(extension.title, 25)}
      onClick={(event) => {
        if (extension.path) {
          return void global.open(locationUtil.assureBaseUrl(extension.path), '_blank');
        }
        extension.onClick?.(event);
      }}
    />
  ));
}

type ExtensionLinksResult = {
  uncategorised: PluginExtensionLink[];
  categorised: Record<string, PluginExtensionLink[]>;
};

function useExtensionLinksByCategory(extensions: PluginExtensionLink[]): ExtensionLinksResult {
  return useMemo(() => {
    const uncategorised: PluginExtensionLink[] = [];
    const categorised: Record<string, PluginExtensionLink[]> = {};

    for (const link of extensions) {
      if (!link.category) {
        uncategorised.push(link);
        continue;
      }

      if (!Array.isArray(categorised[link.category])) {
        categorised[link.category] = [];
      }
      categorised[link.category].push(link);
      continue;
    }

    return {
      uncategorised,
      categorised,
    };
  }, [extensions]);
}
