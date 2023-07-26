from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater


class AlertSlackTemplater(AlertTemplater):
    RENDER_FOR_SLACK = "slack"

    def _render_for(self):
        return self.RENDER_FOR_SLACK

    def _postformat(self, templated_alert):
        # We need to replace new line characters in slack title because slack markdown would break on multiline titles
        if templated_alert.title:
            templated_alert.title = templated_alert.title.replace("\n", "").replace("\r", "")
        return templated_alert

    def render(self):
        """
        Overriden render method to modify payload of manual integration alerts
        """
        self._modify_payload_for_manual_integration_if_needed()
        return super().render()

    def _modify_payload_for_manual_integration_if_needed(self):
        """
        Modifies payload of alerts made from manual incident integration.
        It is needed to simplify templates.
        """
        payload = self.alert.raw_request_data
        # First check if payload look like payload from manual incident integration and was not modified before.
        if "view" in payload and "private_metadata" in payload.get("view", {}) and "oncall" not in payload:
            from apps.alerts.models import AlertReceiveChannel

            # If so - check it with db query.
            if self.alert.group.channel.integration == AlertReceiveChannel.INTEGRATION_MANUAL:
                metadata = payload.get("view", {}).get("private_metadata", {})
                payload["oncall"] = {}
                if "message" in metadata:
                    # If alert was made from message
                    domain = payload.get("team", {}).get("domain", "unknown")
                    channel_id = metadata.get("channel_id", "unknown")
                    message = metadata.get("message", {})
                    message_ts = message.get("ts", "unknown")
                    message_text = message.get("text", "unknown")
                    payload["oncall"]["permalink"] = f"https://{domain}.slack.com/archives/{channel_id}/p{message_ts}"
                    payload["oncall"]["author_username"] = metadata.get("author_username", "Unknown")
                    payload["oncall"]["title"] = "Message from @" + payload["oncall"]["author_username"]
                    payload["oncall"]["message"] = message_text
                else:
                    # If alert was made via slash command
                    message_text = (
                        payload.get("view", {})
                        .get("state", {})
                        .get("values", {})
                        .get("MESSAGE_INPUT", {})
                        .get("FinishCreateIncidentViewStep", {})
                        .get("value", "unknown")
                    )
                    payload["oncall"]["permalink"] = None
                    payload["oncall"]["title"] = self.alert.title
                    payload["oncall"]["message"] = message_text
                    created_by = self.alert.integration_unique_data.get("created_by", None)
                    username = payload.get("user", {}).get("name", None)
                    author_username = created_by or username or "unknown"
                    payload["oncall"]["author_username"] = author_username

                self.alert.raw_request_data = payload
                self.alert.save(update_fields=["raw_request_data"])
