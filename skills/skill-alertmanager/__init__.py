from aiohttp.web import Request

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.events import Message

import logging
import pprint

_LOGGER = logging.getLogger(__name__)

class AlertManager(Skill):
    @match_webhook('webhook')
    async def alertmanager(self, event: Request):
        payload = await event.json()
        _LOGGER.debug('payload receiveddd by alertmanager: ' +
                      pprint.pformat(payload))

        for alert in payload["alerts"]:
            msg = ""
            if "message" in alert["annotations"]:
                msg = alert["annotations"]["message"]
            elif "description" in alert["annotations"]:
                msg = alert["annotations"]["description"]

            if "origin" in alert["labels"]:
                await self.opsdroid.send(Message(str(
                    "{status} {name} ({severity}): {message} in: {origin}".
                    format(
                        status=alert["status"].upper(),
                        name=alert["labels"]["alertname"],
                        severity=alert["labels"]["severity"].upper(),
                        origin=alert["labels"]["origin"].upper(),
                        message=msg)
                )))
            else:
                await self.opsdroid.send(Message(str(
                    "{status} {name} ({severity}): {message}".
                    format(
                        status=alert["status"].upper(),
                        name=alert["labels"]["alertname"],
                        severity=alert["labels"]["severity"].upper(),
                        message=msg)
                )))
