from aiohttp.web import Request

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.events import Message

import json
import logging
import pprint

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=LOGLEVEL)
_LOGGER = logging.getLogger(__name__)


class EventManager(Skill):
    @match_webhook('webhook')
    async def eventmanager(self, opsdroid, config, message):
        if type(message) is Message or type(message) is not Request:
            return

        payload = await message.json()
        _LOGGER.debug('payload received by eventmanager: ' +
                      pprint.pformat(payload))

        message = Message(None,
                          config.get("room",
                                     opsdroid.default_connector.default_room),
                          opsdroid.default_connector,
                          "")

        for alert in payload["alerts"]:
            if alert["status"].upper() == "RESOLVED":
                next
            msg = ""
            if "message" in alert["annotations"]:
                msg = alert["annotations"]["message"]
            elif "description" in alert["annotations"]:
                msg = alert["annotations"]["description"]
            await message.respond("{severity} {name}: {message}".format(
                name=alert["labels"]["alertname"],
                severity=alert["labels"]["severity"].upper(),
                message=msg)
            )
