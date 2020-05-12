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
            template = "New alert: {} in {}"
            if "message" in alert["annotations"]:
                msg = template.format(alert["annotations"]["message"], alert["labels"]["origin"])
            elif "description" in alert["annotations"]:
                msg = template.format(alert["annotations"]["description"], alert["labels"]["origin"])
            await self.opsdroid.send(Message(str(
                "{status} {name} ({severity}): {message}".format(
                    status=alert["status"].upper(),
                    name=alert["labels"]["alertname"],
                    severity=alert["labels"]["severity"].upper(),
                    origin=alert["labels"]["origin"].upper(),
                    message="NEW ALERT!")
                ))
            )
