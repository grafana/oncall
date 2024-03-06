"""
This module provides payloads for heartbeat alerts.
Files from this modules are integrations for which heartbeat is available (if filename not starts with _).
Filename MUST match INTEGRATION_TO_REVERSE_URL_MAP.
"""

import apps.integrations.metadata.heartbeat.alertmanager  # noqa
import apps.integrations.metadata.heartbeat.elastalert  # noqa
import apps.integrations.metadata.heartbeat.formatted_webhook  # noqa
import apps.integrations.metadata.heartbeat.grafana  # noqa
import apps.integrations.metadata.heartbeat.legacy_alertmanager  # noqa
import apps.integrations.metadata.heartbeat.prtg  # noqa
import apps.integrations.metadata.heartbeat.webhook  # noqa
import apps.integrations.metadata.heartbeat.zabbix  # noqa
