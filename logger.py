import functools
import logging
import os
import sys
from typing import Optional

from termcolor import colored


# cache the opened file object, so that different calls to `setup_logger`
# with the same file name can safely write to the same file.
@functools.lru_cache(maxsize=None)
def setup_logger(
    output: Optional[str] = None, distributed_rank: int = 0, *, mode: str = 'w',
    color: bool = True, time: bool = True, name: str = "GCL", abbrev_name: Optional[str] = None
):
    """Initialize the GCL logger and set its verbosity level to "DEBUG".
    Args:
    output : Optional[str], optional
        a file name or a directory to save log. If None, will not save log file.
        If ends with ".txt" or ".log", assumed to be a file name.
        Otherwise, logs will be saved to `output/log.txt`.
    distributed_rank : int, optional
        used for distributed training, by default 0
    mode : str, optional
        mode for the output file (if output is given), by default 'w'.
    color : bool, optional
        whether to use color when printing, by default True
    name : str, optional
        the root module name of this logger, by default "GCL"
    abbrev_name : Optional[str], optional
        an abbreviation of the module, to avoid long names in logs.
        Set to "" to not log the root module in logs.
        By default, None.
    Returns
    -------
    logging.Logger
        a logger
    Example
    -------
    >>> logger = setup_logger(name='my exp')
    >>> logger.info('message')
    [12/19 17:01:43 my exp]: message
    >>> logger.error('message')
    ERROR [12/19 17:02:22 my exp]: message
    >>> logger.warning('message')
    WARNING [12/19 17:02:32 my exp]: message
    >>> # specify output files
    >>> logger = setup_logger(output='log.txt', name='my exp')
    # additive, by default mode='w'
    >>> logger = setup_logger(output='log.txt', name='my exp', mode='a')
    # once you logger is set, you can call it by
    >>> logger = get_logger(name='my exp')
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if abbrev_name is None:
        abbrev_name = name

    plain_formatter = logging.Formatter(
        "[%(asctime)s] %(name)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %H:%M:%S"
    )
    plain_formatter_without_time = logging.Formatter()

    # stdout logging: master only
    if distributed_rank == 0:
        ch = logging.StreamHandler(stream=sys.stdout)
        # ch.setLevel(logging.DEBUG)
        # we change level from logging.debug() to logging.info(), so debug will not be printed to console
        ch.setLevel(logging.INFO)
        if color:
            formatter = _ColorfulFormatter(
                colored("[%(asctime)s %(name)s]: ", "white") + "%(message)s",
                datefmt="%Y/%m/%d %H:%M:%S",
                root_name=name,
                abbrev_name=str(abbrev_name),
            )
        elif time:
            formatter = plain_formatter
        else:
            formatter = plain_formatter_without_time
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    import datetime
    now = datetime.datetime.now()
    # current_time = now.strftime('%Y%m%d%H%M')
    current_time = now.strftime('%Y%m%d%H%M%S')
    dir_time = now.strftime('%Y%m%d')
    # file logging: all workers
    if output is not None:
        if output.endswith(".txt") or output.endswith(".log"):
            filename = output
            dirs = os.path.dirname(filename)
            if dirs:
                if not os.path.isdir(dirs):
                    os.makedirs(dirs)
        else:
            if not os.path.isdir(output + '/' + dir_time):
                os.makedirs(output + '/' + dir_time)
            filename = os.path.join(output, dir_time + '/' + current_time + ".txt")

        if distributed_rank > 0:
            filename = filename + ".rank{}".format(distributed_rank)

        file_handle = logging.FileHandler(filename=filename, mode=mode)
        file_handle.setLevel(logging.DEBUG)
        file_handle.setFormatter(formatter)
        logger.addHandler(file_handle)

    return logger


def get_logger(name: str = "GCL"):
    """Get a logger for a given name.
    Parameters
    ----------
    name : str, optional
        name of the logger, by default "GCL"
    Returns
    -------
    a logger for the given name
    """
    return logging.getLogger(name)


class _ColorfulFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self._root_name = kwargs.pop("root_name") + "."
        self._abbrev_name = kwargs.pop("abbrev_name", "")
        if len(self._abbrev_name):
            self._abbrev_name = self._abbrev_name + "."
        super(_ColorfulFormatter, self).__init__(*args, **kwargs)

    def formatMessage(self, record):
        record.name = record.name.replace(self._root_name, self._abbrev_name)
        log = super(_ColorfulFormatter, self).formatMessage(record)
        if record.levelno == logging.WARNING:
            prefix = colored("WARNING", "red", attrs=["blink"])
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            prefix = colored("ERROR", "red", attrs=["blink", "underline"])
        else:
            return log
        return prefix + " " + log
