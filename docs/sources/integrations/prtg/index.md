---
aliases:
  - add-prtg/
  - /docs/oncall/latest/integrations/available-integrations/configure-prtg/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-prtg/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - prtg
title: PRTG
weight: 500
---

# PRTG integration for Grafana OnCall

The PRTG integration for Grafana OnCall handles ticket events sent from PRTG webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin]({{< relref "user-and-team-management" >}}) to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from PRTG

1. In the **Integrations** tab, click **+ New integration**.
2. Select **PRTG** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring PRTG to Send Alerts to Grafana OnCall

PRTG can use the script to send the alerts to Grafana OnCall. Please use the format below

Body Fields Format:

```plaintext
alert_uid [char][not required] - unique alert ID for grouping;
title [char][not required] - title;
image_url [char][not required] - url for image attached to alert;
state [char][not required] - could be "ok" or "alerting", helpful for auto-resolving;
link_to_upstream_details [char][not required] - link back to your monitoring system;
message [char][not required] - alert details;
```

ps1 script example:

```ps1
# This script sends alerts from PRTG to Grafana OnCall
Param(
  [string]$sensorid,
  [string]$date,
  [string]$device,
  [string]$shortname,
  [string]$status,
  [string]$message,
  [string]$datetime,
  [string]$linksensor,
  [string]$url
)

# PRTG Server
$PRTGServer = "localhost:8080"
$PRTGUsername = "amixr"
$PRTGPasshash  = *****

#Directory for logging
$LogDirectory = "C:\temp\prtg-notifications-msteam.log"

#Acknowledgement Message for alerts ack'd via Teams
$ackmessage = "Problem has been acknowledged via Amixr."

# the acknowledgement URL
$ackURL = [string]::Format("{0}/api/acknowledgealarm.htm?id={1}&ackmsg={2}&username={3}&passhash={4}",
$PRTGServer,$sensorID,$ackmessage,$PRTGUsername,$PRTGPasshash);

# Autoresolve an alert in Amixr
if($status -eq "Up")
{ $state = "ok" }
ElseIf($status -match "now: Up")
{ $state = "ok" }
ElseIf($status -match "Up (was:")
{ $state = "ok" }
Else
{ $state = "alerting" }

$image_datetime = [datetime]::parse($datetime)
$sdate = $image_datetime.AddHours(-1).ToString("yyyy-MM-dd-HH-mm-ss")
$edate = $image_datetime.ToString("yyyy-MM-dd-HH-mm-ss")

$image_url = "$PRTGServer/chart.png?type=graph&graphid=-1&avg=0&width=1000&height=400
&username=$PRTGUsername&passhash=$PRTGPasshash&id=$sensorid&sdate=$sdate&edate=$edate"

$Body = @{
            "alert_uid"="$sensorid $date";
            "title"="$device $shortname $status at $datetime ";
            "image_url"=$image_url;
            "state"=$state;
            "link_to_upstream_details"="$linksensor";
            "message"="$message";
            "ack_url_get"="$ackURL"
} | ConvertTo-Json
$Body

try
{ Invoke-RestMethod -uri $url -Method Post -body $Body -ContentType 'application/json; charset=utf-8'; exit 0; }
Catch
{
    $ErrorMessage = $_.Exception.Message
    (Get-Date).ToString() +" - "+ $ErrorMessage | Out-File -FilePath $LogDirectory -Append
    exit 2;
}

```
