from enum import IntEnum


class CloudSyncStatus(IntEnum):
    NOT_SYNCED = 0
    SYNCED_USER_NOT_FOUND = 1
    SYNCED_PHONE_NOT_VERIFIED = 2
    SYNCED_PHONE_VERIFIED = 3
