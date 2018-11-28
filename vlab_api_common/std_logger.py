# -*- coding: UTF-8 -*-
"""
This simple module allows us to have a consistent logging format across services
"""
import logging


def get_logger(name, loglevel='INFO'):
    """Simple factory function for creating logging objects

    :Returns: logging.Logger

    :param name: The name of the logger (typically just __name__).
    :type name: String

    :param loglevel: The verbosity of the logging; ERROR, INFO, DEBUG
    :type loglevel: String
    """
    logger = logging.getLogger(name)
    logger.setLevel(loglevel.upper())
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        ch.setLevel(loglevel.upper())
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def get_task_logger(txn_id, task_id, loglevel='INFO'):
    """A factory for making a logger that contains a client transaction id, and
    a task id.

    :Returns: logging.Logger

    :param txn_id: The client-supplied transaction id
    :type tx_id: String

    :param task_id: The id of the current task
    :type task_id: String
    """
    extra = {}
    extra['txn_id'] = txn_id
    extra['task_id'] = task_id
    logger = logging.getLogger(task_id)
    logger.setLevel(loglevel.upper())
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(txn_id)s] [%(task_id)s]: %(message)s')
        ch.setLevel(loglevel.upper())
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger = logging.LoggerAdapter(logger, extra)
    return logger
