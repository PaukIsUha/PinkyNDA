import logging, sys, re, colorama  # colorama понадобится только под Windows

colorama.just_fix_windows_console()

RESET = "\033[0m"
CYAN = "\033[36m"
COLORS = {  # базовые цвета по уровню
    logging.DEBUG: "\033[37m",
    logging.INFO: "\033[0m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[41m",
}

PG_RE = re.compile(r'\bpostgresql\b', re.I)


class ColorFormatter(logging.Formatter):
    def format(self, record):
        # цвет по умолчанию — по уровню
        color = COLORS.get(record.levelno, RESET)

        # если INFO и упоминается PostgreSQL → cyan
        if record.levelno == logging.INFO and PG_RE.search(record.getMessage()):
            color = CYAN

        message = super().format(record)
        return f"{color}{message}{RESET}"


handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(ColorFormatter("%(asctime)s %(levelname)-8s | %(message)s"))

log = logging.getLogger("app")
log.setLevel(logging.DEBUG)
log.addHandler(handler)
