from aiohttp.web import Request

from opsdroid.matchers import match_webhook
from opsdroid.events import Message

import logging

_LOGGER = logging.getLogger(__name__)

@match_webhook('webhook')
async def mywebhookskill(opsdroid, config, message):
    if type(message) is not Message and type(message) is Request:
        request = await message.post()

        message = Message("",
                          None,
                          opsdroid.default_connector,
                          config.get("room", opsdroid.default_connector.default_room))

        for key in request.keys():
            _LOGGER.debug('payload received: ' + key)

        await message.respond('Hey')
