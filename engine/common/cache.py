import typing

from django.conf import settings

_RT = typing.TypeVar("_RT", str, typing.List[str], typing.Dict[str, typing.Any])


def ensure_cache_key_allocates_to_the_same_hash_slot(cache_keys: _RT, pattern_to_wrap_in_brackets: str) -> _RT:
    """
    This method will ensure that when using Redis Cluster, multiple cache keys will be allocated to the same hash slot.
    This ensures that multi-key operations (ex `cache.get_many` and `cache.set_many`) will work without raising this
    exception:

    ```
    File "/usr/local/lib/python3.12/site-packages/redis/cluster.py", line 1006, in determine_slot
        raise RedisClusterException(
    redis.exceptions.RedisClusterException: MGET - all keys must map to the same key slot
    ```

    From the Redis Cluster [docs](https://redis.io/docs/reference/cluster-spec/#hash-tags):

    There is an exception for the computation of the hash slot that is used in order to implement hash tags.
    Hash tags are a way to ensure that multiple keys are allocated in the same hash slot.
    This is used in order to implement multi-key operations in Redis Cluster.

    To implement hash tags, the hash slot for a key is computed in a slightly different way in certain conditions.
    If the key contains a "{...}" pattern only the substring between { and } is hashed in order to obtain the hash slot.
    However since it is possible that there are multiple occurrences of { or } the algorithm is well specified by the
    following rules:
    """
    if not settings.USE_REDIS_CLUSTER:
        return cache_keys

    def _replace_key(key: str) -> str:
        return key.replace(pattern_to_wrap_in_brackets, f"{{{pattern_to_wrap_in_brackets}}}")

    if isinstance(cache_keys, str):
        return _replace_key(cache_keys)
    elif isinstance(cache_keys, dict):
        return {_replace_key(key): value for key, value in cache_keys.items()}
    return [_replace_key(key) for key in cache_keys]
