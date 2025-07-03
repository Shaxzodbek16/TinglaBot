from app.core.extensions.utils import WORKDIR
from itertools import cycle
import os

COOKIE_CYCLES = {}


def get_random_cookie(_cookie_type: str) -> str:
    cookies_path = WORKDIR.parent / "static" / "cookie" / _cookie_type
    if _cookie_type not in COOKIE_CYCLES:
        items = os.listdir(cookies_path)
        items.sort()
        COOKIE_CYCLES[_cookie_type] = cycle(items)

    return next(COOKIE_CYCLES[_cookie_type])
