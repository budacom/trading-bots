import logging
import time
from logging import Logger

from .logging import setup_logger
from ..conf import defaults
from ..conf import settings
from ..core.storage import get_store
from ..utils import get_iso_time_str


class Bot:
    """Class representing a base Trading Bot and its logic."""

    label = ''
    verbose_name = ''
    config_file = ''

    def __init__(self, config: dict=None, config_name: str=None, logger: Logger=None):
        assert self.label, 'A Bot object must have a label attribute!'
        # Set configuration
        self.config = config
        self.config_name = config_name or defaults.BOT_CONFIG
        # Set logger
        self.log = logger or logging.getLogger(f'bots.{self.label}')
        self.setup_logger(self.log)
        # Set store
        self.store = get_store(self.log)
        # Configs
        self.dry_run = settings.dry_run
        self.timeout = settings.timeout
        self.env = 'TEST' if self.dry_run else 'LIVE'
        # Time
        self.timestamp = None

    def _setup(self, config):
        raise NotImplementedError

    def _algorithm(self):
        raise NotImplementedError

    def execute(self):
        self.timestamp = int(time.time())
        msg = f'Starting {self.label} {self.timestamp}: {get_iso_time_str()} '
        self.log.info(f'{msg:-<80}')

        try:
            if self.dry_run:
                self.log.warning('DRY RUN!')
            self._setup(self.config)
            self._algorithm()

        except Exception:
            self.log.exception(f'Bot entered an invalid state!')
            self._abort()
            raise

        except KeyboardInterrupt:
            self.log.warning(f'Bot execution cancelled!')
            self._abort()
            raise

        finally:
            run_time = time.time() - self.timestamp
            self.log.info(f'Run time: {run_time:,.4f} seconds')
            msg = f'Ending {self.label} {self.timestamp}: {get_iso_time_str()} '
            self.log.info(f'{msg:-<80}')

    def _abort(self):
        raise NotImplementedError

    def abort(self):
        try:
            self.log.warning(f'Aborting {self.label} bot...')
            self._abort()
        except Exception:
            self.log.critical(f'Failed to abort!!!', exc_info=True)
            raise

    def setup_logger(self, logger: Logger):
        logger_kwargs = self._logger_kwargs()
        setup_logger(logger, logger_name=self.label, **logger_kwargs)

    def _logger_kwargs(self):
        return {'tag': settings.tag, 'bot': self.label, 'config': self.config_name}
