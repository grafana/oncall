import asyncio
import logging

from sys import exit

from nio import AsyncClient, LoginResponse

from apps.matrix.rooms import room_name_normalizer

ROOM_MESSAGE_TYPE = "m.room.message"
TEXT_CONTENT_TYPE = "m.text"

logger = logging.getLogger(__name__)


class MatrixClient(object):
    def __init__(
            self,
            client: AsyncClient
    ):
        self.client = client

    @classmethod
    async def login_with_username_and_password(
            cls,
            user_id: str,  # @user:example.org
            password: str,
            device_name: str,
            homeserver: str
    ):
        """
        TODO: find a way to use OAuth (or some other more-secure-than-passwords-in-env-variables)
        means of logging in
        """
        if not (homeserver.startswith("https://") or homeserver.startswith("http://")):
            homeserver = "https://" + homeserver

        client = AsyncClient(homeserver, user_id)
        resp: LoginResponse = await client.login(password, device_name=device_name)

        # check that we logged in successfully
        if isinstance(resp, LoginResponse):
            return MatrixClient(client)
        else:
            logger.fatal(f'homeserver = "{homeserver}"; user = "{user_id}"')
            logger.fatal(f"Failed to log in: {resp}")
            exit(1)

    @room_name_normalizer()
    async def send_message_to_room(
            self,
            room_name: str,
            raw_body: str,
            formatted_body: str = None):
        if formatted_body is None:
            formatted_body = raw_body

        await self.client.room_send(
            room_id=room_name,
            message_type=ROOM_MESSAGE_TYPE,
            content={
                "msgtype": TEXT_CONTENT_TYPE,
                "body": raw_body,
                "format": "org.matrix.custom.html",
                "formatted_body": formatted_body
            }
        )

    @room_name_normalizer()
    async def join_room(self, room_name: str):
        # This returns a `Union[JoinResponse, JoinError]`, which I think is more Go-style
        # than Pythonic. If we wanted to check return type and take differing action
        # based on that, this would probably be the place to check and throw an Exception.
        # I'll leave it up to the Oncall team what code style they want.
        return await self.client.join(room_name)

    @room_name_normalizer()
    async def is_in_room(self, room_name: str):
        # If we really wanted, we could maintain a set of "joined_rooms" in the client,
        # update it every time `join_room` (or a hypothetical `leave_room`) is called,
        # and avoid a network call for this method. But that complexity doesn't seem
        # worth the latency gain - in particular, note that you'd have to account for
        # room-aliases, which could change without warning, so you'd need to be
        # listening for room update events in order to stay up-to-date. Better, I think,
        # to just go to the source of truth. Until latency becomes a limiting factor - YAGNI
        #
        # See also the comment on `join_room` about Union-type responses encoding success/failure
        return room_name in (await self.client.joined_rooms()).rooms

    async def _normalize_room_name(self, room_name: str) -> str:
        """
        Rooms can be referred to by:
        * a room_id - a single canonical identifier for a room, of the form
            `!<SomeLettersOfVaryingCase>:<homeserver_domain>`
        * a room_alias - of which one room can have many, of the form
            `#<FriendlyName>:<homeserver_domain>`

        This method accepts a name of either(/unknown) type, and normalizes
        to the canonical room_id.

        (Note the intentional use of the noun "name" to encompass both
        `id` and `alias`. If you can think of a better noun, please adopt it!)
        """
        # TODO - repeated points about exceptions vs. Union-type response
        # TODO - (maybe) expand this to accept names without the homeserver domain?
        # Or handle that upstream in the UI and only use, uhh, FQRNs ("Fully-Qualified
        # Room Names" - room-names that always include the homeserver) internally?
        if room_name.startswith("!"):
            return room_name
        normalization_response = await self.client.room_resolve_alias(room_name)
        return normalization_response.room_id
