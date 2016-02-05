import logging

logger = logging.getLogger('__name__')


def catch_exceptions(function):
    def encapsulated_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            return False

    return encapsulated_function
