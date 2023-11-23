import redis.cluster


class RedisClusterShim(redis.cluster.RedisCluster):
    """
    https://stackoverflow.com/a/74269905
    """

    def __init__(self, *args, **kwargs):
        kwargs.pop("connection_pool", None)
        # redis.cluster.NodesManager.initialize() does connection_pool.deepcopy,
        # but redis.connection.ConnectionPool has a _thread.lock, not pickle-able.
        super().__init__(*args, **kwargs)
