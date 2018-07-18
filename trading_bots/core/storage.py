import json as j
import pickle as p
from logging import Logger

from .logging import get_logger
from .utils import load_class_by_name

try:
    import redis
except ImportError:
    pass


def get_store(logger: Logger=None):
    """Get and configure the storage backend"""
    from trading_bots.conf import settings
    store_settings = settings.storage
    store = store_settings.get('name', 'json')
    if store == 'json':
        store = 'trading_bots.core.storage.JSONStore'
    elif store == 'redis':
        store = 'trading_bots.core.storage.RedisStore'
    store_cls = load_class_by_name(store)
    kwargs = store_cls.configure(store_settings)
    return store_cls(logger=logger, **kwargs)


class BaseStore:
    name = ''

    def __init__(self, logger: Logger=None):
        assert self.name, 'A name name must be defined!'
        self.log = logger or get_logger(__name__)

    @classmethod
    def configure(cls, settings):
        """Configure the storage method with app settings"""
        return {}


class Store(BaseStore):
    serializers = {
        'json': j,
        'pickle': p,
    }

    # GET --------------------------------------------------------------------
    def __get(self, method, *path, cast=None, serializer=None, **kwargs):
        path_str = ' '.join(path)
        self.log.debug(f'Get {path_str} from {self.name}')
        try:
            value = method(*path, **kwargs)
            if serializer:
                if isinstance(serializer, str):
                    serializer = self.serializers[serializer]
                return serializer.loads(value)
            if cast:
                return cast(value)
            return value
        except KeyError:
            self.log.warning(f'{path_str} not found on {self.name}')
            return None
        except Exception:
            self.log.exception(f'Failed to get {path_str} from {self.name}')
            raise

    def _get(self, name: str, **kwargs):
        raise NotImplementedError

    def get(self, name: str, cast=None, serializer=None, **kwargs):
        return self.__get(self._get, name, cast=cast, serializer=serializer, **kwargs)

    def _hget(self, name: str, key: str, **kwargs):
        raise NotImplementedError

    def hget(self, name: str, key: str, cast=None, serializer=None, **kwargs):
        return self.__get(self._hget, name, key, cast=cast, serializer=serializer, **kwargs)

    # SET --------------------------------------------------------------------
    def __set(self, method, *path, value, serializer=None, **kwargs):
        path_str = ' '.join(path)
        self.log.debug(f'Set {path_str} on {self.name}')
        try:
            if serializer:
                if isinstance(serializer, str):
                    serializer = self.serializers[serializer]
                value = serializer.dumps(value)
            method(*path, value=value, **kwargs)
        except Exception:
            self.log.exception(f'Failed to set {path_str} on {self.name}')
            raise

    def _set(self, name: str, value, **kwargs):
        raise NotImplementedError

    def set(self, name: str, value, serializer=None, **kwargs):
        return self.__set(self._set, name, value=value, serializer=serializer, **kwargs)

    def _hset(self, name: str, key: str, value, **kwargs):
        raise NotImplementedError

    def hset(self, name: str, key: str, value, serializer=None, **kwargs):
        return self.__set(self._hset, name, key, value=value, serializer=serializer, **kwargs)

    # DELETE -----------------------------------------------------------------
    def __delete(self, method, *path, **kwargs):
        path_str = ' '.join(path)
        self.log.debug(f'Delete {path_str} from {self.name}')
        try:
            method(*path, **kwargs)
        except KeyError:
            self.log.warning(f'{path_str} not found on {self.name}')
            pass
        except Exception:
            self.log.exception(f'Failed to delete {path_str} from {self.name}')
            raise

    def _delete(self, name: str, **kwargs):
        raise NotImplementedError

    def delete(self, name: str, **kwargs):
        return self.__delete(self._delete, name, **kwargs)

    def _hdel(self, name: str, key: str, **kwargs):
        raise NotImplementedError

    def hdel(self, name: str, key: str, **kwargs):
        return self.__delete(self._hdel, name, key, **kwargs)


class JSONStore(Store):
    name = 'JSON File'
    filename = 'store.json'

    def __init__(self, filename: str=None, logger: Logger=None):
        super().__init__(logger)
        if filename is not None:
            self.filename = filename

    @classmethod
    def configure(cls, settings):
        kwargs = super().configure(settings)
        kwargs['filename'] = settings.get('filename')
        return kwargs

    def _read(self):
        try:
            with open(self.filename) as data_file:
                return j.load(data_file)
        except FileNotFoundError:
            self.log.warning(f'File not found! ({self.name})')
            return {}

    def _write(self, value):
        try:
            with open(self.filename, 'w') as outfile:
                j.dump(value, outfile)
        except Exception:
            self.log.exception(f'Failed to write to {self.name}!')
            raise

    def _get(self, name: str, **kwargs):
        data = self._read()
        return data[name]

    def _hget(self, name: str, key: str, **kwargs):
        return self._get(name)[key]

    def _set(self, name: str, value, **kwargs):
        data = self._read()
        data[name] = value
        return self._write(data)

    def _hset(self, name, key, value, **kwargs):
        data = self._read()
        old = data.get(name, {})
        if not isinstance(old, dict):
            old = {}
        data[name] = {**old, key: value}
        return self._write(data)

    def _delete(self, name: str, **kwargs):
        data = self._read() or {}
        data.pop(name)
        return self._write(data)

    def _hdel(self, name: str, key: str, **kwargs):
        data = self._get(name)
        data.pop(key)
        return self._write(data)


class RedisStore(Store):
    name = 'Redis'

    def __init__(self, url: str, logger: Logger=None):
        super().__init__(logger)
        self.r = redis.StrictRedis.from_url(url)

    @classmethod
    def configure(cls, settings):
        kwargs = super().configure(settings)
        kwargs['url'] = settings.get('url')
        return kwargs

    def _get(self, name: str, **kwargs):
        value = self.r.get(name)
        if value is None:
            raise KeyError
        return value

    def _hget(self, name: str, key: str, **kwargs):
        value = self.r.hget(name, key)
        if value is None:
            raise KeyError
        return value

    def _set(self, name: str, value, **kwargs):
        return self.r.set(name, value)

    def _hset(self, name, key, value, **kwargs):
        return self.r.hset(name, key, value)

    def _delete(self, name: str, **kwargs):
        deleted = self.r.delete(name)
        if not deleted:
            raise KeyError
        return deleted

    def _hdel(self, name: str, key: str, **kwargs):
        deleted = self.r.hdel(name, key)
        if not deleted:
            raise KeyError
        return deleted
