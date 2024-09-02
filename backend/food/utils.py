import string
from random import choice, randint

from .constants import MAX_HASH, MIN_HASH


def generate_hash() -> str:
    """Вспомогательная функция для генерации коротких ссылок"""

    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN_HASH, MAX_HASH))
    )
