from aiohttp.web import Request

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.events import Message

import json
import logging

_LOGGER = logging.getLogger(__name__)

class AlertManager(Skill):
    @match_webhook('webhook')
    async def alertmanager(self, opsdroid, config, message):
        if type(message) is not Message and type(message) is Request:
            request = await message.post()

            message = Message(None,
                              config.get("room",
                                         opsdroid.default_connector.default_room),
                              opsdroid.default_connector,
                              "")

            for key in request.keys():
                _LOGGER.debug('payload received: ' + key)

                payload = json.loads(key)

                for alert in payload["alerts"]:
                    await message.respond("Alert *{status}*: {summary} - Severity: `{severity}`".format(
                        status=alert["status"],
                        summary=alert["annotations"]["summary"],
                        severity=alert["labels"]["severity"]))

                    await message.respond("Description: {description}".format(
                        description=alert["annotations"]["description"]))

                    await message.respond("-------------------------------------------------------------")
