import base64
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache
from requests.auth import AuthBase
from requests.models import PreparedRequest

from apps.zoom.exceptions import (
    ZoomAPIChannelNotFoundError,
    ZoomAPIException,
    ZoomAPIRateLimitError,
    ZoomAPITokenInvalid,
    ZoomAPIUserNotFoundError,
)

logger = logging.getLogger(__name__)

# Cache key for Zoom chatbot token
ZOOM_TOKEN_CACHE_KEY = "zoom_chatbot_token"
ZOOM_TOKEN_CACHE_TTL = 3500  # Token expires in 3600s, refresh 100s before


class ZoomBotTokenAuth(AuthBase):
    """Authentication handler for Zoom Bot token."""

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        request.headers["Authorization"] = f"Bearer {self.token}"
        request.headers["Content-Type"] = "application/json"
        return request


@dataclass
class ZoomChatUser:
    """Represents a Zoom user."""
    user_id: str
    email: str
    display_name: str


@dataclass
class ZoomChatChannel:
    """Represents a Zoom Team Chat channel."""
    channel_id: str
    channel_name: str
    channel_type: int  # 1=public, 2=private, 3=instant meeting, 4=direct message


@dataclass
class ZoomChatMessage:
    """Represents a Zoom Team Chat message."""
    message_id: str
    to_channel: str
    robot_jid: str


class ZoomClient:
    """Client for interacting with Zoom Team Chat API."""

    BASE_URL = "https://api.zoom.us/v2"
    CHATBOT_URL = "https://api.zoom.us/v2/im/chat/messages"
    OAUTH_URL = "https://zoom.us/oauth/token"

    def __init__(self, token: Optional[str] = None, robot_jid: Optional[str] = None) -> None:
        self._token = token
        self.robot_jid = robot_jid or getattr(settings, 'ZOOM_BOT_JID', None)
        self.timeout: int = 30

    @property
    def token(self) -> str:
        """Get chatbot token, fetching from OAuth if needed."""
        if self._token:
            return self._token

        # Try to get from cache first
        cached_token = cache.get(ZOOM_TOKEN_CACHE_KEY)
        if cached_token:
            return cached_token

        # Fetch new token via Client Credentials
        token = self._fetch_chatbot_token()
        if token:
            cache.set(ZOOM_TOKEN_CACHE_KEY, token, ZOOM_TOKEN_CACHE_TTL)
            return token

        raise ZoomAPITokenInvalid(msg="Failed to obtain Zoom chatbot token")

    def _fetch_chatbot_token(self) -> Optional[str]:
        """
        Fetch chatbot token using Client Credentials OAuth flow.
        
        POST https://zoom.us/oauth/token?grant_type=client_credentials
        Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)
        """
        client_id = getattr(settings, 'ZOOM_CLIENT_ID', None)
        client_secret = getattr(settings, 'ZOOM_CLIENT_SECRET', None)

        if not client_id or not client_secret:
            logger.error("ZOOM_CLIENT_ID or ZOOM_CLIENT_SECRET not configured")
            return None

        try:
            # Create Basic auth header
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            response = requests.post(
                f"{self.OAUTH_URL}?grant_type=client_credentials",
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            access_token = data.get("access_token")
            
            if access_token:
                logger.info("Successfully obtained Zoom chatbot token")
                return access_token
            else:
                logger.error(f"No access_token in response: {data}")
                return None

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Zoom chatbot token: {e}")
            return None

    def _get_user_jid_from_token(self) -> Optional[str]:
        """
        Extract user_jid from chatbot token by decoding the JWT.
        
        The token contains uid in the body which can be used to construct user_jid.
        user_jid format: user_id@xmpp.zoom.us
        """
        try:
            token = self.token
            if not token:
                return None
            
            # JWT tokens have 3 parts: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode the payload (base64url encoded)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            
            uid = data.get('uid')
            if uid:
                user_jid = f"{uid}@xmpp.zoom.us"
                logger.debug(f"Extracted user_jid from token: {user_jid}")
                return user_jid
            
            return None
        except Exception as e:
            logger.warning(f"Failed to extract user_jid from token: {e}")
            return None

    def _check_response(self, response: requests.models.Response) -> None:
        """Check API response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
        except requests.HTTPError as ex:
            status_code = ex.response.status_code
            try:
                error_msg = ex.response.json().get("message", str(ex))
            except (json.JSONDecodeError, KeyError):
                error_msg = str(ex)

            if status_code == 401:
                raise ZoomAPITokenInvalid(msg=error_msg)
            elif status_code == 404:
                raise ZoomAPIException(
                    status=status_code,
                    url=ex.response.request.url,
                    msg=error_msg,
                    method=ex.response.request.method,
                )
            elif status_code == 429:
                raise ZoomAPIRateLimitError(msg=error_msg)
            else:
                raise ZoomAPIException(
                    status=status_code,
                    url=ex.response.request.url,
                    msg=error_msg,
                    method=ex.response.request.method,
                )
        except requests.Timeout as ex:
            raise ZoomAPIException(
                status=504,
                url=str(ex.request.url) if ex.request else None,
                msg="Zoom API call timed out",
                method=str(ex.request.method) if ex.request else None,
            )
        except requests.exceptions.RequestException as ex:
            raise ZoomAPIException(
                status=500,
                url=str(ex.request.url) if ex.request else None,
                msg=f"Unexpected error from Zoom server: {ex}",
                method=str(ex.request.method) if ex.request else None,
            )

    def get_user(self, user_id: str = "me") -> ZoomChatUser:
        """Get Zoom user information."""
        url = f"{self.BASE_URL}/users/{user_id}"
        response = requests.get(
            url=url,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        data = response.json()
        return ZoomChatUser(
            user_id=data["id"],
            email=data["email"],
            display_name=data.get("display_name", data.get("first_name", "") + " " + data.get("last_name", ""))
        )

    def get_channel(self, channel_id: str) -> ZoomChatChannel:
        """Get Zoom Team Chat channel information."""
        url = f"{self.BASE_URL}/chat/channels/{channel_id}"
        response = requests.get(
            url=url,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        data = response.json()
        return ZoomChatChannel(
            channel_id=data["id"],
            channel_name=data["name"],
            channel_type=data.get("type", 1)
        )

    def send_channel_message(
        self,
        channel_id: str,
        message: str,
        user_jid: Optional[str] = None,
        is_markdown: bool = True,
        interactive_cards: Optional[List[Dict[str, Any]]] = None,
        header_text: str = "OnCall Alert",
        sub_header_text: Optional[str] = None,
    ) -> ZoomChatMessage:
        """
        Send a message to a Zoom Team Chat channel.
        
        For User-managed apps, uses user_jid for authorization.
        For Admin-managed apps, uses account_id.
        
        Reference: https://developers.zoom.us/docs/team-chat/send-edit-and-delete-messages/
        
        Args:
            channel_id: The channel JID (e.g., xxx@conference.xmpp.zoom.us)
            message: The message text
            user_jid: The user JID for user-managed apps (required for user-managed)
            is_markdown: Whether to enable markdown support
            interactive_cards: List of interactive elements (buttons, etc.)
            header_text: Header text for the message card
            sub_header_text: Optional sub-header text
        """
        if not self.robot_jid:
            raise ZoomAPITokenInvalid(msg="Zoom Robot JID is not configured")

        url = self.CHATBOT_URL
        
        # Build base payload
        payload: Dict[str, Any] = {
            "robot_jid": self.robot_jid,
            "to_jid": channel_id,
        }
        
        # For User-managed app, use user_jid; for Admin-managed, use account_id
        account_id = getattr(settings, 'ZOOM_ACCOUNT_ID', None)
        if user_jid:
            payload["user_jid"] = user_jid
        elif account_id:
            payload["account_id"] = account_id
        else:
            raise ZoomAPITokenInvalid(msg="Either user_jid or ZOOM_ACCOUNT_ID must be configured")

        # Build the message content header
        head: Dict[str, Any] = {"text": header_text}
        if sub_header_text:
            head["sub_head"] = {"text": sub_header_text}

        # Build the message content
        if interactive_cards:
            # Use interactive card format for buttons
            body = []
            # Add message text first if provided
            if message:
                body.append({
                    "type": "message",
                    "text": message,
                    "is_markdown_support": is_markdown
                })
            # Add interactive cards (buttons, etc.)
            body.extend(interactive_cards)
            payload["content"] = {"head": head, "body": body}
        else:
            # Use simple message format
            payload["content"] = {
                "head": head,
                "body": [
                    {
                        "type": "message",
                        "text": message,
                        "is_markdown_support": is_markdown
                    }
                ]
            }
        
        if is_markdown:
            payload["is_markdown_support"] = True

        logger.debug(f"Sending message to Zoom channel {channel_id}: {payload}")

        response = requests.post(
            url=url,
            json=payload,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        data = response.json()
        
        return ZoomChatMessage(
            message_id=data.get("message_id", ""),
            to_channel=channel_id,
            robot_jid=self.robot_jid
        )

    def send_channel_message_with_body(
        self,
        channel_id: str,
        header_text: str = "OnCall Alert",
        sub_header_text: Optional[str] = None,
        body: Optional[List[Dict[str, Any]]] = None,
        user_jid: Optional[str] = None,
    ) -> ZoomChatMessage:
        """
        Send a message with full body structure to a Zoom Team Chat channel.
        
        This is useful when you have a pre-built body structure from the renderer.
        Uses ZOOM_ACCOUNT_ID for Admin-managed apps or user_jid for User-managed apps.
        For User-managed apps without explicit user_jid, tries to extract from token.
        """
        if not self.robot_jid:
            raise ZoomAPITokenInvalid(msg="Zoom Robot JID is not configured")

        url = self.CHATBOT_URL
        
        # Build base payload
        payload: Dict[str, Any] = {
            "robot_jid": self.robot_jid,
            "to_jid": channel_id,
        }
        
        # For User-managed app, use user_jid; for Admin-managed, use account_id
        account_id = getattr(settings, 'ZOOM_ACCOUNT_ID', None)
        if user_jid:
            payload["user_jid"] = user_jid
        elif account_id:
            payload["account_id"] = account_id
        else:
            # Try to extract user_jid from token for User-managed apps
            token_user_jid = self._get_user_jid_from_token()
            if token_user_jid:
                payload["user_jid"] = token_user_jid
                logger.info(f"Using user_jid from token: {token_user_jid}")
            else:
                raise ZoomAPITokenInvalid(msg="Either user_jid or ZOOM_ACCOUNT_ID must be configured")

        # Build the message content header
        head: Dict[str, Any] = {"text": header_text}
        if sub_header_text:
            head["sub_head"] = {"text": sub_header_text}

        # Build content with full body (sidebar_color is set in body sections)
        payload["content"] = {
            "head": head,
            "body": body or []
        }
        payload["is_markdown_support"] = True

        logger.debug(f"Sending message with body to Zoom channel {channel_id}")

        response = requests.post(
            url=url,
            json=payload,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        data = response.json()
        
        return ZoomChatMessage(
            message_id=data.get("message_id", ""),
            to_channel=channel_id,
            robot_jid=self.robot_jid
        )

    def update_message(
        self,
        message_id: str,
        channel_id: str,
        message: str,
        user_jid: Optional[str] = None,
        is_markdown: bool = True,
        interactive_cards: Optional[List[Dict[str, Any]]] = None,
        header_text: str = "OnCall Alert",
        sub_header_text: Optional[str] = None,
    ) -> ZoomChatMessage:
        """
        Update an existing message in a Zoom Team Chat channel.
        
        Reference: https://developers.zoom.us/docs/team-chat/send-edit-and-delete-messages/
        """
        if not self.robot_jid:
            raise ZoomAPITokenInvalid(msg="Zoom Robot JID is not configured")

        url = f"{self.CHATBOT_URL}/{message_id}"
        
        # Build base payload
        payload: Dict[str, Any] = {
            "robot_jid": self.robot_jid,
            "to_jid": channel_id,
        }
        
        # For User-managed app, use user_jid; for Admin-managed, use account_id
        account_id = getattr(settings, 'ZOOM_ACCOUNT_ID', None)
        if user_jid:
            payload["user_jid"] = user_jid
        elif account_id:
            payload["account_id"] = account_id
        else:
            raise ZoomAPITokenInvalid(msg="Either user_jid or ZOOM_ACCOUNT_ID must be configured")

        # Build the message content header
        head: Dict[str, Any] = {"text": header_text}
        if sub_header_text:
            head["sub_head"] = {"text": sub_header_text}

        # Build the message content
        if interactive_cards:
            body = []
            if message:
                body.append({
                    "type": "message",
                    "text": message,
                    "is_markdown_support": is_markdown
                })
            body.extend(interactive_cards)
            payload["content"] = {"head": head, "body": body}
        else:
            payload["content"] = {
                "head": head,
                "body": [
                    {
                        "type": "message",
                        "text": message,
                        "is_markdown_support": is_markdown
                    }
                ]
            }
        
        if is_markdown:
            payload["is_markdown_support"] = True

        logger.debug(f"Updating message {message_id} in Zoom channel {channel_id}")

        response = requests.put(
            url=url,
            json=payload,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        
        return ZoomChatMessage(
            message_id=message_id,
            to_channel=channel_id,
            robot_jid=self.robot_jid
        )

    def update_message_with_body(
        self,
        message_id: str,
        channel_id: str,
        user_jid: Optional[str] = None,
        header_text: str = "OnCall Alert",
        sub_header_text: Optional[str] = None,
        body: Optional[List[Dict[str, Any]]] = None,
    ) -> ZoomChatMessage:
        """
        Update an existing message with full body structure.
        
        This method allows passing a complete body structure instead of
        building it from message + interactive_cards.
        """
        if not self.robot_jid:
            raise ZoomAPITokenInvalid(msg="Zoom Robot JID is not configured")

        url = f"{self.CHATBOT_URL}/{message_id}"
        
        # Build base payload
        payload: Dict[str, Any] = {
            "robot_jid": self.robot_jid,
            "to_jid": channel_id,
        }
        
        # For User-managed app, use user_jid; for Admin-managed, use account_id
        account_id = getattr(settings, 'ZOOM_ACCOUNT_ID', None)
        if user_jid:
            payload["user_jid"] = user_jid
        elif account_id:
            payload["account_id"] = account_id
        else:
            # Try to extract user_jid from token for User-managed apps
            token_user_jid = self._get_user_jid_from_token()
            if token_user_jid:
                payload["user_jid"] = token_user_jid
                logger.info(f"Using user_jid from token for update: {token_user_jid}")
            else:
                raise ZoomAPITokenInvalid(msg="Either user_jid or ZOOM_ACCOUNT_ID must be configured")

        # Build the message content header
        head: Dict[str, Any] = {"text": header_text}
        if sub_header_text:
            head["sub_head"] = {"text": sub_header_text}

        # Build content with full body (sidebar_color is set in body sections)
        payload["content"] = {
            "head": head,
            "body": body or []
        }
        payload["is_markdown_support"] = True

        logger.debug(f"Updating message {message_id} with body")

        response = requests.put(
            url=url,
            json=payload,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        
        return ZoomChatMessage(
            message_id=message_id,
            to_channel=channel_id,
            robot_jid=self.robot_jid
        )

    def delete_message(self, message_id: str, channel_id: str) -> bool:
        """
        Delete a message from a Zoom Team Chat channel.
        """
        if not self.robot_jid:
            raise ZoomAPITokenInvalid(msg="Zoom Robot JID is not configured")

        url = f"{self.CHATBOT_URL}/{message_id}"
        
        params = {
            "robot_jid": self.robot_jid,
            "to_channel": channel_id,
            "account_id": getattr(settings, 'ZOOM_ACCOUNT_ID', ''),
        }

        response = requests.delete(
            url=url,
            params=params,
            timeout=self.timeout,
            auth=ZoomBotTokenAuth(self.token)
        )
        self._check_response(response)
        
        return True

    def list_channels(self, page_size: int = 50) -> List[ZoomChatChannel]:
        """List all Zoom Team Chat channels the bot has access to."""
        url = f"{self.BASE_URL}/chat/channels"
        channels = []
        next_page_token = None

        while True:
            params = {"page_size": page_size}
            if next_page_token:
                params["next_page_token"] = next_page_token

            response = requests.get(
                url=url,
                params=params,
                timeout=self.timeout,
                auth=ZoomBotTokenAuth(self.token)
            )
            self._check_response(response)
            data = response.json()

            for channel_data in data.get("channels", []):
                channels.append(ZoomChatChannel(
                    channel_id=channel_data["id"],
                    channel_name=channel_data["name"],
                    channel_type=channel_data.get("type", 1)
                ))

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

        return channels
