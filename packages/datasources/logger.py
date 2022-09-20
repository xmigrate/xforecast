import logging,sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
def logger(message, type):
    if type == "debug":
        logging.debug(message)
    elif type == "warning":
        logging.warning(message)
    elif type == "info":
        logging.info(message)
    elif type == "error":
        logging.error(message)
    elif type == "critical":
        logging.critical(message)