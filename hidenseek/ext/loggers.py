import logging


formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
LOGGING_DASHES = "===================="


# https://stackoverflow.com/a/11233293
def setup_logger(name, log_file, level=logging.WARNING, console=False):
    """
    Setups logger for future usage

    Parameters
    ----------
        name : string
            logger name
        log_file : string
            path to file where logs should be saved
        level : logging.LEVEL
            built-in logging levels, default: logging.WARNING
        console : bool
            whenever logs should also be printed in console
    """
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    if console:
        handler_console = logging.StreamHandler()
        handler_console.setFormatter(formatter)
        logger.addHandler(handler_console)

    return logger

logger_seeker = setup_logger('logger_agent_seeker', 'logs/agent_seeker.log', logging.INFO)
logger_hiding = setup_logger('logger_agent_hiding', 'logs/agent_hiding.log', logging.INFO)
logger_engine = setup_logger('logger_engine', 'logs/engine.log', level=logging.INFO, console=True)