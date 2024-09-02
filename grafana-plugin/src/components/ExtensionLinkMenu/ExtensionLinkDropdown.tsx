import React, { ReactElement, useEffect, useMemo, useState } from 'react';

import { PluginExtensionLink, SelectableValue } from '@grafana/data';
import {
  type GetPluginExtensionsOptions,
  getPluginLinkExtensions,
  usePluginLinks as originalUsePluginLinks,
} from '@grafana/runtime';
import { Button, Dropdown, Modal, Select, Stack, ToolbarButton } from '@grafana/ui';
import { OnCallPluginExtensionPoints } from 'app-types';

import { ApiSchemas } from 'network/oncall-api/api.types';

import { ExtensionLinkMenu } from './ExtensionLinkMenu';
import { toJS } from 'mobx';
import { useStore } from 'state/useStore';
import { alertGroupDynamicLabelCheatSheet } from 'components/CheatSheet/CheatSheet.config';
import { StackSize } from 'utils/consts';
import { SelectOption } from 'state/types';
import { ActionKey } from 'models/loader/action-keys';
import { observer } from 'mobx-react';
import { openErrorNotification, openNotification } from 'utils/utils';

interface Props {
  alertGroup: ApiSchemas['AlertGroup'];
  extensionPointId: OnCallPluginExtensionPoints;
  declareIncidentLink?: string;
  grafanaIncidentId: string | null;
}

// `usePluginLinks()` is only available in Grafana>=11.1.0, so we have a fallback for older versions
const usePluginLinks = originalUsePluginLinks === undefined ? usePluginLinksFallback : originalUsePluginLinks;

export function ExtensionLinkDropdown({
  alertGroup,
  extensionPointId,
  declareIncidentLink,
  grafanaIncidentId,
}: Props): ReactElement | null {
  const [isOpen, setIsOpen] = useState(false);
  const [isTriggerWebhookModalOpen, setIsTriggerWebhookModalOpen] = useState(false);
  const context = useExtensionPointContext(alertGroup);
  const { links, isLoading } = usePluginLinks({ context, extensionPointId, limitPerPlugin: 3 });

  if (isLoading) {
    return null;
  }

  const onOpenTriggerWebhookModal = async () => {
    setIsOpen(false);
    setIsTriggerWebhookModalOpen(true);
  };

  const menu = (
    <ExtensionLinkMenu
      extensions={links}
      triggerWebhookModal={{
        onOpenModal: onOpenTriggerWebhookModal,
      }}
      declareIncidentLink={declareIncidentLink}
      grafanaIncidentId={grafanaIncidentId}
    />
  );

  return (
    <div>
      <TriggerManualWebhook
        alertGroup={alertGroup}
        isModalOpen={isTriggerWebhookModalOpen}
        setIsModalOpen={setIsTriggerWebhookModalOpen}
      />

      <Dropdown onVisibleChange={setIsOpen} placement="bottom-start" overlay={menu}>
        <ToolbarButton aria-label="Actions" variant="canvas" isOpen={isOpen}>
          Actions
        </ToolbarButton>
      </Dropdown>
    </div>
  );
}

interface TriggerManualWebhookProps {
  alertGroup: ApiSchemas['AlertGroup'];
  isModalOpen: boolean;
  setIsModalOpen: (isOpen: boolean) => void;
}

const TriggerManualWebhook = observer(({ isModalOpen, setIsModalOpen, alertGroup }: TriggerManualWebhookProps) => {
  const store = useStore();
  const [selectedWebhookOption, setSelectedWebhookOption] = useState<SelectableValue<string>>(null);

  useEffect(() => {
    (async () => {
      if (isModalOpen) {
        await store.outgoingWebhookStore.updateItems({
          trigger_type: 0,
          integration: alertGroup.alert_receive_channel.id,
        });
      }
    })();
  }, [isModalOpen]);

  return (
    <Modal isOpen={isModalOpen} title={'Select outgoing webhook to trigger'} onDismiss={() => setIsModalOpen(false)}>
      <Stack direction="column" gap={StackSize.lg}>
        <Select
          isLoading={store.loaderStore.isLoading(ActionKey.FETCH_WEBHOOKS)}
          menuShouldPortal
          value={selectedWebhookOption}
          onChange={(option) => setSelectedWebhookOption(option)}
          options={Object.values(store.outgoingWebhookStore.items).map((item) => ({
            label: item.name,
            value: item.id,
          }))}
        />

        <Stack gap={StackSize.md} justifyContent={'flex-end'}>
          <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={onTriggerWebhook}
            disabled={store.loaderStore.isLoading(ActionKey.TRIGGER_MANUAL_WEBHOOK)}
          >
            Trigger webhook
          </Button>
        </Stack>
      </Stack>
    </Modal>
  );

  async function onTriggerWebhook() {
    await store.outgoingWebhookStore.triggerManualWebhook(selectedWebhookOption.value, alertGroup.pk);
    setIsModalOpen(false);
  }
});

function useExtensionPointContext(incident: ApiSchemas['AlertGroup']): PluginExtensionOnCallAlertGroupContext {
  return { alertGroup: incident };
}

function usePluginLinksFallback({ context, extensionPointId, limitPerPlugin }: GetPluginExtensionsOptions): {
  links: PluginExtensionLink[];
  isLoading: boolean;
} {
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
