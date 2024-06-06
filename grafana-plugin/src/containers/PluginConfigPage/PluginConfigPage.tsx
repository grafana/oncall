import React from 'react';

import { PluginConfigPageProps, PluginMeta } from '@grafana/data';
import { config } from '@grafana/runtime';
import { Field, HorizontalGroup, Input } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import { Controller, useForm } from 'react-hook-form';
import { OnCallPluginMetaJSONData } from 'types';

import { Button } from 'components/Button/Button';
import { getOnCallApiUrl } from 'utils/consts';
import { validateURL } from 'utils/string';

type PluginConfigFormValues = {
  onCallApiUrl: string;
};

export const PluginConfigPage = observer((props: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
  const { handleSubmit, control, formState } = useForm<PluginConfigFormValues>({
    mode: 'onChange',
    defaultValues: { onCallApiUrl: getOnCallApiUrl(props.plugin.meta) },
  });

  const onSubmit = (values: PluginConfigFormValues) => {
    // eslint-disable-next-line no-console
    console.log(values);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        name={'onCallApiUrl'}
        control={control}
        rules={{ required: 'OnCall API URL is required', validate: validateURL }}
        render={({ field }) => (
          <Field
            key={'Name'}
            label={'OnCall API URL'}
            invalid={Boolean(formState.errors.onCallApiUrl)}
            error={formState.errors.onCallApiUrl?.message}
          >
            <Input {...field} placeholder={'OnCall API URL'} data-testid="oncall-api-url-input" />
          </Field>
        )}
      />
      <HorizontalGroup>
        <Button type="submit" disabled={!formState.isValid}>
          Test & Save connection
        </Button>
        {config.featureToggles.externalServiceAccounts && <Button variant="secondary">Recreate service account</Button>}
      </HorizontalGroup>
    </form>
  );
});
