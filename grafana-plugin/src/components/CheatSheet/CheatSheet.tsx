import React from 'react';

import { IconButton, Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { openNotification } from 'helpers/helpers';
import CopyToClipboard from 'react-copy-to-clipboard';
import { bem, getUtilStyles } from 'styles/utils.styles';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';

import { CheatSheetInterface, CheatSheetItem } from './CheatSheet.config';
import { getCheatSheetStyles } from './CheatSheet.styles';

interface CheatSheetProps {
  cheatSheetName: string;
  cheatSheetData: CheatSheetInterface;
  onClose: () => void;
}

export const CheatSheet = (props: CheatSheetProps) => {
  const { cheatSheetName, cheatSheetData, onClose } = props;

  const styles = useStyles2(getCheatSheetStyles);
  const utils = useStyles2(getUtilStyles);

  return (
    <div className={styles.cheatsheetContainer}>
      <div className={styles.cheatsheetInnerContainer}>
        <Stack direction="column">
          <Stack justifyContent="space-between">
            <Text strong>{cheatSheetName} cheatsheet</Text>
            <IconButton aria-label="Close" name="times" onClick={onClose} />
          </Stack>
          <Text type="secondary">{cheatSheetData.description}</Text>
          <div className={utils.width100}>
            {cheatSheetData.fields?.map((field: CheatSheetItem) => {
              return (
                <div key={field.name} className={styles.cheatsheetItem}>
                  <CheatSheetListItem field={field} />
                </div>
              );
            })}
          </div>
        </Stack>
      </div>
    </div>
  );
};

interface CheatSheetListItemProps {
  field: CheatSheetItem;
}
const CheatSheetListItem = (props: CheatSheetListItemProps) => {
  const { field } = props;
  const styles = useStyles2(getCheatSheetStyles);

  return (
    <>
      <Text>{field.name}</Text>
      {field.listItems?.map((item, key) => {
        return (
          <div key={key}>
            <Stack direction="column" gap={StackSize.md}>
              {item.listItemName && (
                <li style={{ margin: '0 0 0 4px' }}>
                  <Text>{item.listItemName}</Text>
                </li>
              )}
              {item.codeExample && (
                <div className={bem(styles.cheatsheetItem, 'small')}>
                  <Block bordered fullWidth withBackground>
                    <Stack justifyContent="space-between">
                      <Text type="link" className={styles.code}>
                        {item.codeExample}
                      </Text>
                      <CopyToClipboard text={item.codeExample} onCopy={() => openNotification('Example copied')}>
                        <IconButton aria-label="Copy" name="copy" />
                      </CopyToClipboard>
                    </Stack>
                  </Block>
                </div>
              )}
            </Stack>
          </div>
        );
      })}
    </>
  );
};
