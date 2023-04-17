import React from 'react';

import { HorizontalGroup, IconButton, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { openNotification } from 'utils';

import { CheatSheetInterface, CheatSheetItem } from './CheatSheet.config';

import styles from './CheatSheet.module.css';

interface CheatSheetProps {
  cheatSheetData: CheatSheetInterface;
  onClose: () => void;
}

const cx = cn.bind(styles);

const CheatSheet = (props: CheatSheetProps) => {
  const { cheatSheetData, onClose } = props;
  return (
    <div className={cx('cheatsheet-container')}>
      <VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text.Title level={5}>{cheatSheetData.name}</Text.Title>
          <IconButton name="times" onClick={onClose} />
        </HorizontalGroup>
        <Text type="secondary">{cheatSheetData.description}</Text>
        <div>
          {cheatSheetData.fields?.map((field: CheatSheetItem) => {
            return (
              <div key={field.name} className={cx('cheatsheet-item')}>
                <CheatSheetListItem field={field} />
              </div>
            );
          })}
        </div>
      </VerticalGroup>
    </div>
  );
};

interface CheatSheetListItemProps {
  field: CheatSheetItem;
}
const CheatSheetListItem = (props: CheatSheetListItemProps) => {
  const { field } = props;
  return (
    <>
      <Text.Title level={6}>{field.name}</Text.Title>
      {field.listItems?.map((item, key) => {
        return (
          <div key={key}>
            <VerticalGroup>
              {item.listItemName && <Text>- {item.listItemName}</Text>}
              {item.codeExample && (
                <Block bordered withBackground>
                  <HorizontalGroup justify="space-between">
                    <Text type="link">{item.codeExample}</Text>
                    <CopyToClipboard text={item.codeExample} onCopy={() => openNotification('Example copied')}>
                      <IconButton name="copy" />
                    </CopyToClipboard>
                  </HorizontalGroup>
                </Block>
              )}
            </VerticalGroup>
          </div>
        );
      })}
    </>
  );
};

export default CheatSheet;
