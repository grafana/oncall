import React, { FC, useCallback, useEffect, useState } from 'react';

import { Button, HorizontalGroup, Select, SelectValue, VerticalGroup } from '@grafana/ui';
import { capitalCase } from 'change-case';

import { useStore } from 'state/useStore';

interface ServiceLabelsProps {}

const generateOptions = (serviceLabelName: string) => {
  const count = Math.floor(Math.random() * 20) + 1;
  const arr = [];
  for (let i = 0; i < count; i++) {
    arr.push({
      label: capitalCase(serviceLabelName) + ' ' + (i + 1),
      value: serviceLabelName + i + 1,
    });
  }
  return arr;
};

interface ServiceLabelOption {
  name: string;
  options: Array<SelectValue<string>>;
}

interface ServiceLabel {
  name: ServiceLabelOption['name'];
  value: string;
}

const predefinedLabelOptions = {
  team: generateOptions('team'),
  project: generateOptions('project'),
  billing: generateOptions('billing'),
  customer: generateOptions('customer'),
};

const Labels: FC<ServiceLabelsProps> = () => {
  const store = useStore();

  const updateLabels = () => {
    store.labelsStore.updateKeys().then((data) => {
      const value = data.map((key) => ({ name: key.repr, value: key.id }));
      setServiceLabels(value);
    });
  };

  useEffect(updateLabels, []);

  const handleLabelCreate = useCallback(() => {
    const name = prompt();
    store.labelsStore.createLabel({ key: { repr: name }, values: [] }).then(updateLabels);
  }, []);

  const getServiceLabelDeleteHandler = (serviceLabelName) => {
    return () => {
      setServiceLabels((serviceLabels) => serviceLabels.filter((sl) => sl.name !== serviceLabelName));
    };
  };
  const getServiceLabelNameChangeHandler = (serviceLabelName) => {
    return ({ value }) => {
      const serviceLabelIndex = serviceLabels.findIndex((sl) => sl.name === serviceLabelName);

      setServiceLabels((serviceLabels) => {
        const newServiceLabels = [...serviceLabels];
        newServiceLabels[serviceLabelIndex] = {
          name: value,
          value: undefined,
        };

        return newServiceLabels;
      });
    };
  };

  const getServiceLabelChangeHandler = (serviceLabelName) => {
    return ({ value }) => {
      const serviceLabelIndex = serviceLabels.findIndex((sl) => sl.name === serviceLabelName);

      setServiceLabels((serviceLabels) => {
        const newServiceLabels = [...serviceLabels];
        newServiceLabels[serviceLabelIndex].value = value;

        return newServiceLabels;
      });
    };
  };

  const getCreateNewLabelOptionHandler = (serviceLabelName) => {
    return (value) => {
      const customValue = value.toLowerCase();

      setLabelOptions((labelOptions) => ({
        ...labelOptions,
        [customValue]: generateOptions(customValue),
      }));

      const serviceLabelIndex = serviceLabels.findIndex((sl) => sl.name === serviceLabelName);

      setServiceLabels((serviceLabels) => {
        const newServiceLabels = [...serviceLabels];
        newServiceLabels[serviceLabelIndex].name = customValue;

        return newServiceLabels;
      });
    };
  };

  /* const handleLabelAdd = () => {
    setServiceLabels((serviceLabels) => [...serviceLabels, { name: undefined, value: undefined }]);
  }; */

  const [labelOptions, setLabelOptions] = useState(predefinedLabelOptions);

  const [serviceLabels, setServiceLabels] = useState<ServiceLabel[]>([]);

  return (
    <VerticalGroup>
      {serviceLabels.map((serviceLabel, index) => (
        <HorizontalGroup key={index}>
          <Select
            //@ts-ignore
            width={'200px'}
            value={serviceLabel.value}
            options={serviceLabels.map((label) => ({ label: label.name, value: label.value }))}
            onChange={getServiceLabelNameChangeHandler(serviceLabel.name)}
            placeholder="Select key"
            autoFocus
            allowCustomValue
            onCreateOption={getCreateNewLabelOptionHandler(serviceLabel.name)}
          />
          <Select
            //@ts-ignore
            width={'200px'}
            disabled={!serviceLabel.name}
            value={serviceLabel.value}
            options={labelOptions[serviceLabel.name]}
            onChange={getServiceLabelChangeHandler(serviceLabel.name)}
            placeholder={serviceLabel.name ? 'Select value' : 'Select key first'}
            autoFocus
          />
          <Button
            disabled={false}
            tooltip="Remove label"
            variant="secondary"
            icon="times"
            size="sm"
            onClick={getServiceLabelDeleteHandler(serviceLabel.name)}
          />
          {index === serviceLabels.length - 1 && (
            <Button
              disabled={false}
              size="sm"
              tooltip="Add label"
              variant="secondary"
              icon="plus"
              onClick={handleLabelCreate}
            />
          )}
        </HorizontalGroup>
      ))}
      {!serviceLabels.length && (
        <Button disabled={false} tooltip="Add label" variant="primary" icon="plus" onClick={handleLabelCreate}>
          Label
        </Button>
      )}
    </VerticalGroup>
  );
};

export default Labels;
