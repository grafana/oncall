+++
title = "Manage alert groups"
description = ""
keywords = ["Grafana", "oncall", "on-call", "calendar", "incidents", "alert groups"]
weight = 300
+++

# Manage alert groups

When you create a new alert integration, alerts are sent from the alert monitoring service of that source to Grafana OnCall. When the first alert is sent, the escalation policies you have in place for that integration determine when and where notifications are sent. Alerts will continue to gather until resolved, forming an alert group. For example, if Juan, an administrator, silences a firing alert group, the alerts will continue to collect in that group until the status is **resolved**. Once this occurs, a new alert will begin the next alert group. 

In the **Alert Groups** tab, you can view alert groups by status. Groups are named by the name of the first alert that was fired. When you click on a group, you can view information on all of alerts that have fired, the source of the alerts, and the users assigned in the escalation chain associated with the group. You can also view the timeline of the group, which shows all of the actions associated with the configured escalation policies, and resolution notes. 

Administrators can change the status of individual alert groups, or can select multiple groups to edit at once. Alert group status can be changed in the following ways: `acknowledge`, `resolve`, `unresolve`, `restart`, and `silence`.