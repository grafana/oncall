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
          <Text strong>{cheatSheetData.name}</Text>
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
      <Text>{field.name}</Text>
      {field.listItems?.map((item, key) => {
        return (
          <div key={key}>
            <VerticalGroup spacing="md">
              {item.listItemName && (
                <li style={{ margin: '0 0 0 4px' }}>
                  <Text>{item.listItemName}</Text>
                </li>
              )}
              {item.codeExample && (
                <div className={cx('cheatsheet-item-small')}>
                  <Block bordered fullWidth withBackground>
                    <HorizontalGroup justify="space-between">
                      <Text type="link">{item.codeExample}</Text>
                      <CopyToClipboard text={item.codeExample} onCopy={() => openNotification('Example copied')}>
                        <IconButton name="copy" />
                      </CopyToClipboard>
                    </HorizontalGroup>
                  </Block>
                </div>
              )}
            </VerticalGroup>
          </div>
        );
      })}
    </>
  );
};

export default CheatSheet;
