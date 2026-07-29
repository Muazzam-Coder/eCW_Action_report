import os
import sys
import datetime
import logging

LOG_DIR = os.path.join(os.path.expanduser("~"), "Documents", "action_report")


class TeeWriter:
    def __init__(self, logger):
        self.logger = logger
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)
        if message.strip():
            self.logger.info(message.strip())

    def flush(self):
        self.terminal.flush()


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    today = datetime.date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"action_report_{today}.log")

    cutoff = datetime.date.today() - datetime.timedelta(days=7)
    for f in os.listdir(LOG_DIR):
        if f.startswith("action_report_") and f.endswith(".log"):
            try:
                date_str = f.replace("action_report_", "").replace(".log", "")
                file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if file_date < cutoff:
                    os.remove(os.path.join(LOG_DIR, f))
            except ValueError:
                pass

    logger = logging.getLogger("action_report")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(handler)

    sys.stdout = TeeWriter(logger)
