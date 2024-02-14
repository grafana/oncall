import React, { FC } from 'react';

import { LabelTag } from '@grafana/labels';
import { VerticalGroup, HorizontalGroup, Button } from '@grafana/ui';

import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { LabelKeyValue } from 'models/label/label.types';

interface LabelsTooltipBadgeProps {
  labels: LabelKeyValue[];
  onClick: (label: LabelKeyValue) => void;
}

export const LabelsTooltipBadge: FC<LabelsTooltipBadgeProps> = ({ labels, onClick }) =>
  labels.length ? (
    <TooltipBadge
      borderType="secondary"
      icon="tag-alt"
      addPadding
      text={labels?.length}
      tooltipContent={
        <VerticalGroup spacing="sm">
          {labels.map((label) => (
            <HorizontalGroup spacing="sm" key={label.key.id}>
              <LabelTag label={label.key.name} value={label.value.name} />
              <Button
                size="sm"
                icon="filter"
                tooltip="Apply filter"
                variant="secondary"
                onClick={() => onClick(label)}
              />
            </HorizontalGroup>
          ))}
        </VerticalGroup>
      }
    />
  ) : null;
