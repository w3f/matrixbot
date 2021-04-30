from opsdroid.skill import Skill
from opsdroid.matchers import match_parse
from opsdroid.matchers import match_crontab
from opsdroid.matchers import match_webhook
from aiohttp.web import Request
from opsdroid.events import Message
import uuid
import logging
import pprint

_LOGGER = logging.getLogger(__name__)
ESCALATION_LIMIT = 3

class EventManagerAck(Skill):

    @match_webhook('webhook-ack')
    async def eventmanager_ack(self, event: Request):
        payload = await event.json()
        _LOGGER.debug('payload received by eventmanager: ' + pprint.pformat(payload))

        for alert in payload["alerts"]:
            if alert["status"].upper() == "RESOLVED":
                continue
            msg = ""
            if "message" in alert["annotations"]:
                msg = alert["annotations"]["message"]
            elif "description" in alert["annotations"]:
                msg = alert["annotations"]["description"]

            toBeStored = {
              "uuid": uuid.uuid4().hex,
              "severity": alert["labels"]["severity"].upper(),
              "name": alert["labels"]["alertname"],
              "message": msg,
              "reminder_counter": 0,
            }

            await self.store_alert(toBeStored)
            await self.opsdroid.send(Message(self.build_event_message(toBeStored)))    

    #TOCHANGE every minute for testing pourposes
    @match_crontab('*/1 * * * *', timezone="Europe/Rome")
    async def crontab_show_pending(self, event):
        pending = await self.get_pending_alerts()
        if pending:
          await self.opsdroid.send(Message(text="NOTE: Some confirmations still require your attention:"))
          for p in pending:
              if p["reminder_counter"] == ESCALATION_LIMIT
                await self.opsdroid.send(Message(self.build_escalation_message(p)))
              else
                await self.opsdroid.send(Message(self.build_event_message(p)))

    @match_parse('!pending')
    async def pending_alerts(self, message):
        _LOGGER.info(f"SKILL: ACK pending called")
        
        pending = await self.get_pending_alerts()
        await self.log_alert(pending)
        await message.respond("Pending alerts:")
        for p in pending:
              await self.opsdroid.send(Message(self.build_event_message(p)))      

    # Alias for `!acknowledge`
    @match_parse('!ack {uuid}')
    async def ack(self, message):
        self.acknowledge(message)

    @match_parse('!acknowledge {uuid}')
    async def acknowledge(self, message):
        uuid = message.entities['uuid']['value']
        _LOGGER.info(f"SKILL: ACK confirm called with uuid {uuid}")

        isFound = await self.delete_by_uuid(uuid)
        if isFound == True:
            await message.respond("Confirmation Success: {}".format(uuid))
        else:
            await message.respond("No match found for this ID: {}".format(uuid))

    async def get_pending_alerts(self):
        pending = await self.opsdroid.memory.get("pending_alerts")
        if pending is None:
          pending = []
        return pending

    async def store_alert(self, toBeStored):
        pending = await self.get_pending_alerts()
        pending.append(toBeStored)
        await self.opsdroid.memory.put("pending_alerts", pending)
        _LOGGER.info(f"DB: Stored {toBeStored}")
        await self.log_db_state()

    async def log_db_state(self):
        pending = await self.get_pending_alerts()
        _LOGGER.info(f"DB: current state, pending acks:")
        for ack in pending:
            _LOGGER.info(f"{ack}")    

    async def log_alert(self, alerts):
        _LOGGER.info(f"SKILL: alerts:")
        for alert in alerts:
            _LOGGER.info(f"{alert}")

    async def delete_by_uuid(self, uuid):
        pending = await self.get_pending_alerts()
        isFound = False
        for p in pending:
            if p["uuid"] == uuid:
                pending.remove(p)
                await self.opsdroid.memory.put("pending_alerts", pending_alerts)
                isFound = True
                _LOGGER.info(f"DB: Deleted {p}")
                await self.log_db_state()
        return isFound   

    def build_event_message(self, ack):
        return str(
            "{severity} {name}: {message}\nPlease provide a acknowledgment using the following command: '!ack:confirm {uuid}' ".format(
                name=alert["name"],
                severity=alert["severity"],
                message=alert["message"],
                uuid=alert["uuid"]
            ))

    def build_escalation_message(self, alert):
        return str(
            "ESCALATION: notifying relevant authorities about the following incident: {severity} {name}: {message}".format(
                name=alert["name"],
                severity=alert["severity"],
                message=alert["message"],
            ))