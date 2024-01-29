import React, { FC } from 'react';

import { Button, Field, HorizontalGroup, Input, useStyles2, VerticalGroup } from '@grafana/ui';
import { useForm } from 'react-hook-form';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';

import { getStyles } from './OutgoingTab.styles';

interface UrlSettingsDrawerContentProps {
  closeDrawer: () => void;
}

export const UrlSettingsDrawerContent: FC<UrlSettingsDrawerContentProps> = ({ closeDrawer }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ mode: 'all' });
  const styles = useStyles2(getStyles);

  const onSubmit = (data) => console.log(data);

  // TODO: define validation rules with backend team

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
      <VerticalGroup justify="space-between">
        <div className={styles.formFieldsWrapper}>
          <Field
            label="Service Now URL"
            invalid={Boolean(errors?.serviceNowUrl?.message)}
            error={errors?.serviceNowUrl?.message}
          >
            <Input
              placeholder="Enter Service Now URL"
              {...register('serviceNowUrl', {
                required: 'Service Now URL is required',
                maxLength: { message: 'Service Now URL is too long', value: 100 },
              })}
            />
          </Field>
          <Field
            label="Authorization header"
            invalid={Boolean(errors?.authorizationHeader?.message)}
            error={errors?.authorizationHeader?.message}
          >
            <Input
              placeholder="Enter authorization header"
              {...register('authorizationHeader', {
                maxLength: { message: 'Authorization header is too long', value: 100 },
              })}
            />
          </Field>
          <Button variant="secondary" onClick={() => {}}>
            Test
          </Button>
        </div>
        <div className={styles.bottomButtons}>
          <HorizontalGroup justify="flex-end">
            <Button variant="secondary" onClick={closeDrawer}>
              Close
            </Button>
            <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
              <Button type="submit">Update</Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </div>
      </VerticalGroup>
    </form>
  );
};
