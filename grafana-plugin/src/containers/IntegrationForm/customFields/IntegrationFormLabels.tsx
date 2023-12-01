import React, { FC } from 'react';

import { CustomFieldSectionRendererProps } from 'components/GForm/GForm';
import RenderConditionally from 'components/RenderConditionally/RenderConditionally';
import { IntegrationFormFieldName } from 'containers/IntegrationForm/IntegrationForm.types';
import Labels, { LabelsProps } from 'containers/Labels/Labels';
import { LabelKeyValue } from 'models/label/label.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

const IntegrationFormLabels: FC<CustomFieldSectionRendererProps> = ({ setValue, getValues, errors }) => {
  const { hasFeature } = useStore();
  const onDataUpdate: LabelsProps['onDataUpdate'] = (val) => setValue(IntegrationFormFieldName.Labels, val);

  return (
    <RenderConditionally shouldRender={hasFeature(AppFeature.Labels)}>
      <Labels
        value={getValues<LabelKeyValue[]>('labels') || []}
        errors={errors?.[IntegrationFormFieldName.Labels]}
        onDataUpdate={onDataUpdate}
      />
    </RenderConditionally>
  );
};

export default IntegrationFormLabels;
