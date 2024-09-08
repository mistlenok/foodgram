import hashlib

from .constants import MAX_HASH


def generate_short_link(recipe_id):
    """Вспомогательная функция для генерации коротких ссылок"""
    hash_object = hashlib.md5(str(recipe_id).encode())
    return hash_object.hexdigest()[:MAX_HASH]
