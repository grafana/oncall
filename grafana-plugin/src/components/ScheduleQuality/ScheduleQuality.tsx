import React, { FC, useEffect } from 'react';

import { cx } from '@emotion/css';
import { Tooltip, VerticalGroup, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { getUtilStyles } from 'styles/utils.styles';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { ScheduleQualityDetails } from 'components/ScheduleQualityDetails/ScheduleQualityDetails';
import { Tag, TagColor } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { Schedule, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import { getScheduleQualityStyles } from './ScheduleQuality.styles';

interface ScheduleQualityProps {
  schedule: Schedule;
}

export const ScheduleQuality: FC<ScheduleQualityProps> = observer(({ schedule }) => {
  const styles = useStyles2(getScheduleQualityStyles);
  const utils = useStyles2(getUtilStyles);

  const {
    scheduleStore: { getScoreQuality, relatedEscalationChains, quality },
  } = useStore();

  useEffect(() => {
    if (schedule.id) {
      getScoreQuality(schedule.id);
    }
  }, [schedule.id]);

  if (!quality) {
    return null;
  }

  const relatedScheduleEscalationChains = relatedEscalationChains[schedule.id];

  return (
    <>
      <div className={styles.root} data-testid="schedule-quality">
        {relatedScheduleEscalationChains?.length > 0 && schedule?.number_of_escalation_chains > 0 && (
          <TooltipBadge
            borderType="success"
            icon="link"
            addPadding
            text={schedule.number_of_escalation_chains}
            tooltipTitle="Used in escalations"
            tooltipContent={
              <VerticalGroup spacing="sm">
                {relatedScheduleEscalationChains.map((escalationChain) => (
                  <div key={escalationChain.pk}>
                    <PluginLink query={{ page: 'escalations', id: escalationChain.pk }} className="link">
                      <Text type="link">{escalationChain.name}</Text>
                    </PluginLink>
                  </div>
                ))}
              </VerticalGroup>
            }
          />
        )}

        {schedule.warnings?.length > 0 && (
          <TooltipBadge
            borderType="warning"
            icon="exclamation-triangle"
            addPadding
            text={schedule.warnings.length}
            tooltipTitle="Warnings"
            tooltipContent={
              <VerticalGroup spacing="none">
                {schedule.warnings.map((warning, index) => (
                  <Text type="primary" key={index}>
                    {warning}
                  </Text>
                ))}
              </VerticalGroup>
            }
          />
        )}

        <Tooltip
          placement="bottom-start"
          interactive
          content={<ScheduleQualityDetails quality={quality} getScheduleQualityString={getScheduleQualityString} />}
        >
          <div className={cx(utils.cursorDefault)}>
            <Tag className={styles.tag} color={getTagSeverity()}>
              Quality: <strong>{getScheduleQualityString(quality.total_score)}</strong>
            </Tag>
          </div>
        </Tooltip>
      </div>
    </>
  );

  function getScheduleQualityString(score: number): ScheduleScoreQualityResult {
    if (score < 20) {
      return ScheduleScoreQualityResult.Bad;
    }
    if (score < 40) {
      return ScheduleScoreQualityResult.Low;
    }
    if (score < 60) {
      return ScheduleScoreQualityResult.Medium;
    }
    if (score < 80) {
      return ScheduleScoreQualityResult.Good;
    }
    return ScheduleScoreQualityResult.Great;
  }

  function getTagSeverity() {
    if (quality?.total_score < 20) {
      return TagColor.ERROR_LABEL;
    }
    if (quality?.total_score < 60) {
      return TagColor.WARNING_LABEL;
    }
    return TagColor.SUCCESS_LABEL;
  }
});
