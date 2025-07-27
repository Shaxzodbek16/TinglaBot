from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.utils.i18n import I18n


class I18nTextFilter(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message, i18n: I18n) -> bool:
        return message.text == i18n.gettext(self.key)
