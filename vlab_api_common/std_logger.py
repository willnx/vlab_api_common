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
