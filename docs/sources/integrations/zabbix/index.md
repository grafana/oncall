---
aliases:
  - add-zabbix/
canonical: https://grafana.com/docs/oncall/latest/integrations/zabbix/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Zabbix
title: Zabbix
weight: 500
---

# Zabbix integration for Grafana OnCall

Zabbix is an open-source monitoring software tool for diverse IT components, including networks, servers, virtual
machines, and cloud services. Zabbix provides monitoring for metrics such as network utilization, CPU load, and disk
space consumption.

## Configure Zabbix integration for Grafana OnCall

This integration is available for Grafana Cloud OnCall. You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Zabbix** from the list of available integrations
3. Follow the instructions in the **How to connect** window to get your unique integration URL and review next steps.

<!--![123](../_images/connect-new-monitoring.png)-->

## Configure the Zabbix server

1. Deploy a Zabbix playground if you don't have one set up:

   ```bash
    docker run --name zabbix-appliance -t \
         -p 10051:10051 \
         -p 80:80 \
         -d zabbix/zabbix-appliance:latest
   ```

2. Establish an ssh connection to a Zabbix server.

   ```bash
   docker exec -it zabbix-appliance bash
   ```

3. Place the [grafana_oncall.sh](#grafana_oncallsh-script) script in the `AlertScriptsPath` directory specified within
   the Zabbix server configuration file (zabbix_server.conf).

   ```bash
   grep AlertScriptsPath /etc/zabbix/zabbix_server.conf
   ```

   > **Note:** The script must be executable by the user running the zabbix_server binary (usually "zabbix") on the
   > Zabbix server. For example, `chmod +x grafana_oncall.sh`

   ```bash
   ls -lh /usr/lib/zabbix/alertscripts/grafana_oncall.sh
   -rw-r--r--    1 root     root        1.5K Jun  6 07:52 /usr/lib/zabbix/alertscripts/grafana_oncall.sh
   ```

## Configure Zabbix alerts

Within Zabbix web interface, do the following:

1. In a browser, open localhost:80.

2. Navigate to **Adminitstration > Media Types > Create Media Type**.

   <!--![](../_images/zabbix-1.png)-->

3. Create a Media Type with the following fields.

   - Name: Grafana OnCall
   - Type: script
   - Script parameters:
     - {ALERT.SENDTO}
     - {ALERT.SUBJECT}
     - {ALERT.MESSAGE}

   <!--![](../_images/zabbix-2.png)-->

### Set the {ALERT.SEND_TO} value

To send alerts to Grafana OnCall, the {ALERT.SEND_TO} value must be set in the [user media configuration](https://www.zabbix.com/documentation/3.4/manual/config/notifications/media/script#user_media).

1. In the web UI, navigate to **Administration > Users** and open the **user properties** form.

2. In the **Media** tab, click **Add** and copy the link from Grafana OnCall in the `Send to` field.

   <!--![](../_images/zabbix-7.png)-->

3. Click **Test** in the last column to send a test alert to Grafana OnCall.

   <!--![](../_images/zabbix-3.png)-->

4. Specify **Send to** OnCall using the unique integration URL from the above step in the testing window that opens.  
   Create a test message with a body and optional subject and click **Test**.

   <!--![](../_images/zabbix-4.png)

        WHERE DID SLACK COME FROM?! 1. View the Grafana OnCall incident that appears in the Slack channel.
       ![](../_images/zabbix-5.png)-->

## Grouping and auto-resolve of Zabbix notifications

Grafana OnCall provides grouping and auto-resolve of Zabbix notifications.
Use the following procedure to configure grouping and auto-resolve.

1. Provide a parameter as an identifier for group differentiation to Grafana OnCall.

2. Append that variable to the subject of the action as `ONCALL_GROUP: ID`, where `ID` is any of the Zabbix [macros](https://www.zabbix.com/documentation/4.2/manual/appendix/macros/supported_by_location).
   For example, `{EVENT.ID}`. The Grafana OnCall script [grafana_oncall.sh](#grafana_oncallsh-script) extracts this event
   and passes the `alert_uid` to Grafana OnCall.

3. To enable auto-resolve within Grafana Oncall, the "Resolved" keyword is required in the **Default subject** field
   in **Recovered operations**.

<!--![](../_images/zabbix-6.png)-->

## grafana_oncall.sh script

```bash
#!/bin/bash
# This is the modification of original ericos's shell script.

# Get the url ($1), subject ($2), and message ($3)
url="$1"
subject="${2//$'\r\n'/'\n'}"
message="${3//$'\r\n'/'\n'}"

# Alert state depending on the subject indicating whether it is a trigger going in to problem state or recovering
recoversub='^RECOVER(Y|ED)?$|^OK$|^Resolved.*'

if [[ "$subject" =~ $recoversub ]]; then
    state='ok'
else
    state='alerting'
fi

payload='{
    "title": "'${subject}'",
    "state": "'${state}'",
    "message": "'${message}'"
}'

# Alert group identifier from the subject of action. Grouping will not work without ONCALL_GROUP in the action subject
regex='ONCALL_GROUP: ([a-zA-Z0-9_\"]*)'
if [[ "$subject" =~ $regex ]]; then
    alert_uid=${BASH_REMATCH[1]}
    payload='{
        "alert_uid": "'${alert_uid}'",
        "title": "'${subject}'",
        "state": "'${state}'",
        "message": "'${message}'"
    }'
fi

return=$(curl $url -d "${payload}" -H "Content-Type: application/json" -X POST)
```

## More Information

For more information on Zabbix scripts, see [scripts for notifications](https://www.zabbix.com/documentation/4.2/manual/config/notifications/media/script).
