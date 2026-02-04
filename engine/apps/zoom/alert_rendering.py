import os
import time
from typing import Any, Dict, List, Optional, Tuple

from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from apps.alerts.models import Alert, AlertGroup
from apps.zoom.events.types import EventAction
from apps.zoom.utils import ZoomEventAuthenticator
from common.api_helpers.utils import create_engine_url
from common.utils import is_string_with_visible_characters, str_or_backup


class ZoomMessageRenderer:
    """Renderer for Zoom Team Chat messages."""

    def __init__(self, alert_group: AlertGroup):
        self.alert_group = alert_group

    def render_alert_group_message(
        self,
        action_user_name: Optional[str] = None,
        action_user_jid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Render an alert group as a Zoom message.
        
        Args:
            action_user_name: The Zoom display name of the user who performed the action.
            action_user_jid: The Zoom JID of the user, used for @ mention.
        
        Returns a dict with:
        - header: Header text
        - sub_header: Sub-header text with alert info
        - body: List of body elements for Zoom card
        """
        renderer = AlertGroupZoomRenderer(self.alert_group)
        return renderer.render_alert_group_dict(
            action_user_name=action_user_name,
            action_user_jid=action_user_jid,
        )

    def render_alert_group_card(self) -> List[Dict[str, Any]]:
        """Render an alert group as Zoom card body format."""
        renderer = AlertGroupZoomRenderer(self.alert_group)
        return renderer.render_alert_group_card()

    def render_alert_group_text(self) -> str:
        """Render an alert group as plain text."""
        renderer = AlertGroupZoomRenderer(self.alert_group)
        return renderer.render_alert_group_text()


class AlertZoomTemplater(AlertTemplater):
    """Templater for Zoom alert messages."""
    RENDER_FOR_ZOOM = "zoom"

    def _render_for(self) -> str:
        return self.RENDER_FOR_ZOOM


class AlertZoomRenderer(AlertBaseRenderer):
    """Renderer for individual alerts in Zoom format."""

    def __init__(self, alert: Alert):
        super().__init__(alert)
        self.channel = alert.group.channel

    @property
    def templater_class(self):
        return AlertZoomTemplater

    def render_alert_text(self) -> str:
        """Render alert as text."""
        title = str_or_backup(self.templated_alert.title, "Alert")
        message = ""
        if is_string_with_visible_characters(self.templated_alert.message):
            message = f"\n{self.templated_alert.message}"
        
        source_link = ""
        if self.templated_alert.source_link:
            source_link = f"\n[View Source]({self.templated_alert.source_link})"
        
        return f"**{title}**{message}{source_link}"


class AlertGroupZoomRenderer(AlertGroupBaseRenderer):
    """Renderer for alert groups in Zoom format."""

    def __init__(self, alert_group: AlertGroup):
        super().__init__(alert_group)
        self.alert_renderer = self.alert_renderer_class(self.alert_group.alerts.last())

    @property
    def alert_renderer_class(self):
        return AlertZoomRenderer

    def render_alert_group_text(self) -> str:
        """Render alert group as plain text."""
        text = self.alert_renderer.render_alert_text()
        alert_group = self.alert_group

        if alert_group.resolved:
            text += f"\n\n✅ {alert_group.get_resolve_text()}"
        elif alert_group.acknowledged:
            text += f"\n\n⏸️ {alert_group.get_acknowledge_text()}"
        else:
            text += f"\n\n🚨 Status: Firing"

        text += f"\n\nAlerts: {alert_group.alerts.count()}"
        
        return text

    def render_alert_group_card(self) -> List[Dict[str, Any]]:
        """
        Render alert group as Zoom interactive card format.
        
        Reference: https://developers.zoom.us/docs/team-chat-apps/send-and-edit-chatbot-messages/
        """
        alert_group = self.alert_group
        templated_alert = self.alert_renderer.templated_alert
        
        # Determine status color and emoji
        if alert_group.resolved:
            status_emoji = "✅"
            status_text = "Resolved"
            color = "#2eb886"  # Green
        elif alert_group.acknowledged:
            status_emoji = "⏸️"
            status_text = "Acknowledged"
            color = "#808080"  # Gray
        elif alert_group.silenced:
            status_emoji = "🔇"
            status_text = "Silenced"
            color = "#9400D3"  # Purple
        else:
            status_emoji = "🚨"
            status_text = "Firing"
            color = "#a30200"  # Red

        # Build the card body
        body = []

        # Title section
        title = str_or_backup(templated_alert.title, "Alert")
        body.append({
            "type": "message",
            "text": f"**{title}**",
            "is_markdown_support": True,
        })

        # Message content
        if is_string_with_visible_characters(templated_alert.message):
            body.append({
                "type": "message",
                "text": templated_alert.message,
                "is_markdown_support": True,
            })

        # Status section
        body.append({
            "type": "message",
            "text": f"{status_emoji} **Status:** {status_text}",
            "is_markdown_support": True,
        })

        # Additional info
        if alert_group.resolved:
            body.append({
                "type": "message",
                "text": alert_group.get_resolve_text(),
                "is_markdown_support": True,
            })
        elif alert_group.acknowledged:
            body.append({
                "type": "message",
                "text": alert_group.get_acknowledge_text(),
                "is_markdown_support": True,
            })

        # Alert count
        body.append({
            "type": "message",
            "text": f"📊 **Alerts:** {alert_group.alerts.count()}",
            "is_markdown_support": True,
        })

        # Source link
        if templated_alert.source_link:
            body.append({
                "type": "message",
                "text": f"[View Source]({templated_alert.source_link})",
                "is_markdown_support": True,
            })

        # Add action buttons
        main_buttons, silence_buttons = self._get_action_buttons()
        
        # Combine main buttons with silence overflow in one row
        if silence_buttons:
            all_buttons = main_buttons + silence_buttons
            body.append({
                "type": "actions",
                "limit": len(main_buttons),  # Show only main buttons, silence in overflow
                "items": all_buttons,
                "overflow": {
                    "text": "🔇 Silence"
                }
            })
        else:
            body.append({
                "type": "actions",
                "items": main_buttons
            })

        return body

    def render_alert_group_dict(
        self,
        action_user_name: Optional[str] = None,
        action_user_jid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Render alert group as a dict for Zoom message update.
        
        Args:
            action_user_name: The Zoom display name of the user who performed the action.
            action_user_jid: The Zoom JID for @ mention.
        
        Returns:
            {
                "header": "OnCall Alert",
                "sub_header": "#123 AlertName [status]",
                "body": [list of body elements for Zoom card],
                "color": "#hex color for sidebar",
            }
        """
        alert_group = self.alert_group
        templated_alert = self.alert_renderer.templated_alert
        
        # Determine status and sidebar color
        if alert_group.resolved:
            status_text = "RESOLVED"
            status_emoji = "✅"
            color = "#2eb886"  # Green
        elif alert_group.acknowledged:
            status_text = "ACKNOWLEDGED"
            status_emoji = "⏸️"
            color = "#808080"  # Gray
        elif alert_group.silenced:
            status_text = "SILENCED"
            status_emoji = "🔇"
            color = "#9400D3"  # Purple
        else:
            status_text = "FIRING"
            status_emoji = "🔴"
            color = "#a30200"  # Red
        
        # Build header and sub-header
        title = str_or_backup(templated_alert.title, "Incident")
        header = "OnCall Alert"
        sub_header = f"#{alert_group.inside_organization_number} Incident [{status_text.lower()}] {status_emoji}"
        
        # Build section content with sidebar color
        sections = []
        
        # Status section
        sections.append({
            "type": "message",
            "text": f"*Status:* {status_emoji} {status_text}",
            "is_markdown_support": True
        })
        
        # Alert title/name
        sections.append({
            "type": "message",
            "text": f"*Alert:* {title}",
            "is_markdown_support": True
        })
        
        # Status details (who acknowledged/resolved) - use Zoom @ mention if jid provided
        if alert_group.resolved:
            if action_user_jid and action_user_name:
                # Use Zoom @ mention syntax: <!user_jid|Name>
                user_mention = f"<!{action_user_jid}|{action_user_name}>"
                status_detail = f"Resolved by {user_mention}"
            elif action_user_name:
                status_detail = f"Resolved by {action_user_name}"
            else:
                status_detail = alert_group.get_resolve_text()
            sections.append({
                "type": "message",
                "text": f"_{status_detail}_",
                "is_markdown_support": True
            })
        elif alert_group.acknowledged:
            if action_user_jid and action_user_name:
                # Use Zoom @ mention syntax: <!user_jid|Name>
                user_mention = f"<!{action_user_jid}|{action_user_name}>"
                status_detail = f"Acknowledged by {user_mention}"
            elif action_user_name:
                status_detail = f"Acknowledged by {action_user_name}"
            else:
                status_detail = alert_group.get_acknowledge_text()
            sections.append({
                "type": "message",
                "text": f"_{status_detail}_",
                "is_markdown_support": True
            })
        
        # Add action buttons to sections
        main_buttons, silence_buttons = self._get_action_buttons()
        
        # Combine main buttons with silence overflow in one row
        if silence_buttons:
            # Add all main buttons first, then silence buttons
            all_buttons = main_buttons + silence_buttons
            sections.append({
                "type": "actions",
                "limit": len(main_buttons),  # Show only main buttons, silence in overflow
                "items": all_buttons,
                "overflow": {
                    "text": "🔇 Silence"
                }
            })
        else:
            # No silence options, just main buttons
            sections.append({
                "type": "actions",
                "items": main_buttons
            })
        
        # Build body with section containing sidebar_color
        footer_text = os.environ.get("ZOOM_MESSAGE_FOOTER", "OnCall Alert System")
        footer_icon = os.environ.get("ZOOM_MESSAGE_FOOTER_ICON", "")
        
        section_content = {
            "type": "section",
            "sidebar_color": color,
            "sections": sections,
            "footer": footer_text,
            "ts": int(time.time() * 1000)
        }
        
        # Only add footer_icon if configured
        if footer_icon:
            section_content["footer_icon"] = footer_icon
        
        body = [section_content]
        
        return {
            "header": header,
            "sub_header": sub_header,
            "body": body,
        }

    # Silence delay options: (seconds, display_text)
    SILENCE_OPTIONS = [
        (1800, "30 minutes"),
        (3600, "1 hour"),
        (7200, "2 hours"),
        (14400, "4 hours"),
        (21600, "6 hours"),
        (43200, "12 hours"),
        (86400, "24 hours"),
        (-1, "Forever"),
    ]

    def _get_action_buttons(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate action buttons for the alert group.
        
        Returns:
            Tuple of (main_buttons, silence_buttons)
        """
        main_buttons = []
        silence_buttons = []
        alert_pk = self.alert_group.public_primary_key

        if not self.alert_group.resolved:
            if self.alert_group.acknowledged:
                main_buttons.append({
                    "text": "↩️ Unacknowledge",
                    "value": f"unack_{alert_pk}",
                    "style": "Default",
                })
            else:
                main_buttons.append({
                    "text": "✅ Acknowledge",
                    "value": f"ack_{alert_pk}",
                    "style": "Primary",
                })
            
            # Silence buttons with time options (if not already silenced)
            if not self.alert_group.silenced:
                for delay_seconds, display_text in self.SILENCE_OPTIONS:
                    silence_buttons.append({
                        "text": display_text,  # No emoji, shown in overflow menu
                        "value": f"silence_{delay_seconds}_{alert_pk}",
                        "style": "Default",
                    })
            else:
                # Unsilence button when silenced
                main_buttons.append({
                    "text": "🔔 Unsilence",
                    "value": f"unsilence_{alert_pk}",
                    "style": "Default",
                })

        if self.alert_group.resolved:
            main_buttons.append({
                "text": "↩️ Unresolve",
                "value": f"unresolve_{alert_pk}",
                "style": "Default",
            })
        else:
            main_buttons.append({
                "text": "✔️ Resolve",
                "value": f"resolve_{alert_pk}",
                "style": "Primary" if self.alert_group.acknowledged else "Default",
            })

        return main_buttons, silence_buttons
