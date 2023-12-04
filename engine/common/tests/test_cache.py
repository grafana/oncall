from django.test import override_settings

from common.cache import ensure_cache_key_allocates_to_the_same_hash_slot

PATTERN = "schedule_oncall_users"
NON_EXISTENT_PATTERN = "nmzxcnvmzxcv"
NUM_CACHE_KEYS = 5
SINGLE_CACHE_KEY = f"{PATTERN}_0"
CACHE_KEYS = [f"{PATTERN}_{pk}" for pk in range(NUM_CACHE_KEYS)]
SET_MANY_CACHE_KEYS_DICT = {k: "foo" for k in CACHE_KEYS}


def test_ensure_cache_key_allocates_to_the_same_hash_slot() -> None:
    def _convert_key(key: str) -> str:
        return key.replace(PATTERN, f"{{{PATTERN}}}")

    # when USE_REDIS_CLUSTER is False the method should just return the cache keys
    with override_settings(USE_REDIS_CLUSTER=False):
        assert ensure_cache_key_allocates_to_the_same_hash_slot(SINGLE_CACHE_KEY, PATTERN) == SINGLE_CACHE_KEY
        assert ensure_cache_key_allocates_to_the_same_hash_slot(CACHE_KEYS, PATTERN) == CACHE_KEYS
        assert (
            ensure_cache_key_allocates_to_the_same_hash_slot(SET_MANY_CACHE_KEYS_DICT, PATTERN)
            == SET_MANY_CACHE_KEYS_DICT
        )

    # when USE_REDIS_CLUSTER is True the method should wrap the specified pattern within the cache keys in curly brackets
    with override_settings(USE_REDIS_CLUSTER=True):
        # works with a single str cache key
        assert ensure_cache_key_allocates_to_the_same_hash_slot(SINGLE_CACHE_KEY, PATTERN) == _convert_key(
            SINGLE_CACHE_KEY
        )

        # works with a list (useful for cache.get_many operations)
        assert ensure_cache_key_allocates_to_the_same_hash_slot(CACHE_KEYS, PATTERN) == [
            _convert_key(k) for k in CACHE_KEYS
        ]

        # works with a dict (useful for cache.set_many operations)
        assert ensure_cache_key_allocates_to_the_same_hash_slot(SET_MANY_CACHE_KEYS_DICT, PATTERN) == {
            _convert_key(k): v for k, v in SET_MANY_CACHE_KEYS_DICT.items()
        }

        # if the pattern doesn't exist, we don't wrap it in brackets
        assert (
            ensure_cache_key_allocates_to_the_same_hash_slot(SINGLE_CACHE_KEY, NON_EXISTENT_PATTERN) == SINGLE_CACHE_KEY
        )
        assert ensure_cache_key_allocates_to_the_same_hash_slot(CACHE_KEYS, NON_EXISTENT_PATTERN) == CACHE_KEYS
        assert (
            ensure_cache_key_allocates_to_the_same_hash_slot(SET_MANY_CACHE_KEYS_DICT, NON_EXISTENT_PATTERN)
            == SET_MANY_CACHE_KEYS_DICT
        )
