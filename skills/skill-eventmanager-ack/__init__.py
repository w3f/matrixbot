import uuid as uuid_pkg
import logging
import pprint
import time
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse, match_crontab, match_webhook
from aiohttp.web import Request
from opsdroid.events import Message
from opsdroid.constraints import constrain_rooms

_LOGGER = logging.getLogger(__name__)

def build_event_message(alert, is_escalation):
    """Build an alert notification message."""
    prefix = ""
    if alert["counter"] > 0:
        prefix += "Reminder: "
    if is_escalation:
        prefix += "ESCALATION "

    return str(
        "{prefix}{severity} {name}: {message} \nPlease provide a acknowledgment using the following command: \"ack {uuid}\"".format(
            prefix=prefix,
            name=alert["name"],
            severity=alert["severity"],
            message=alert["message"],
            uuid=alert["uuid"]
        ))

def build_escalation_occurred(alert, notify_authorities):
    extra = ""
    if notify_authorities:
        extra += "notifying relevant authorities about the following incident: "

    """Build an esclation message."""
    return str(
        "ESCALATION occurred: {extra}{severity} {name}: {message}".format(
            extra=extra,
            name=alert["name"],
            severity=alert["severity"],
            message=alert["message"]
        ))

class EventManagerAck(Skill):
    def __init__(self, opsdroid, config):
        super(EventManagerAck, self).__init__(opsdroid, config)
        self.EventManagerAck = constrain_rooms(self.config.get("escalation_rooms"))

    @match_webhook('webhook-ack')
    async def eventmanager_ack(self, event: Request):
        """Alert webhook. Store the alerts in the database."""
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

            alert_context = {
                "uuid": uuid_pkg.uuid4().hex,
                "severity": alert["labels"]["severity"].upper(),
                "name": alert["labels"]["alertname"],
                "message": msg,
                "counter": 0,
                "room_index": -1,
            }

            await self.store_alert(alert_context)
            await self.opsdroid.send(Message(build_event_message(alert_context, False)))

    #every hour
    @match_crontab('0 * * * *', timezone="Europe/Rome")
    async def crontab_show_pending(self, _):
        """Notify users about the pending alerts."""
        pending = await self.get_pending_alerts()
        escalation_rooms = self.config.get("escalation_rooms")
        escalation_threshold = self.config.get("escalation_threshold")

        if pending:
            for alert in pending:
                pending.remove(alert)
                alert["counter"] += 1
                room_index = alert["room_index"]

                if alert["counter"] >= escalation_threshold and len(escalation_rooms) - 1 > room_index:
                    # Warn current room about escalation.
                    _LOGGER.info(f"ESCALATION: {alert}")
                    if room_index == -1:
                        await self.opsdroid.send(Message(build_escalation_occurred(alert, True)))
                    else:
                        await self.opsdroid.send(Message(text=build_escalation_occurred(alert, True), target=escalation_rooms[room_index]))

                    # Increment room index (escalations levels).
                    alert["room_index"] += 1
                    alert["counter"] = 0

                    next_room = escalation_rooms[alert["room_index"]]
                    _LOGGER.info(f"Notifying room {next_room} about escalation")
                    await self.opsdroid.send(Message(text=build_escalation_occurred(alert, False), target=next_room))
                else:
                    if room_index == -1:
                        await self.opsdroid.send(Message(build_event_message(alert, False)))
                    else:
                        # Send escalation message to corresponding escalation room.
                        await self.opsdroid.send(Message(text=build_event_message(alert, True), target=escalation_rooms[room_index]))

                pending.append(alert)

        # Add back updated entries
        await self.opsdroid.memory.put("pending_alerts", pending)

    @match_parse('help')
    async def help(self, message):
        await message.respond((
            "\"ack ALERT_ID\" - Acknowledge the the given alert.\n"
            "\"pending\" - Show list of pending alerts.\n"
            "\"escalated\" - Show list of escalated alerts."
        ))

    @match_parse('pending')
    async def pending_alerts(self, message):
        """Respond with pending alerts."""
        _LOGGER.info(f"SKILL: 'pending' called")

        pending = await self.get_pending_alerts()
        if pending:
            # First, get a list of alerts that qualify.
            to_send = []
            for alert in pending:
                # Room index '0' imples non-escalation.
                if alert["room_index"] == -1:
                    to_send.append(alert)

            # If there are some alerts that qualify, notify room.
            if to_send:
                await message.respond("Pending alerts:")
                time.sleep(1)

                for alert in to_send:
                    await message.respond(Message(build_event_message(alert, False)))
            else:
                await message.respond("There are no pending alerts")
        else:
            await message.respond("There are no pending alerts")

    @match_parse('escalated')
    async def escalations(self, message):
        """Respond with escalations."""
        _LOGGER.info(f"SKILL: 'escalated' called")

        escalated = await self.get_pending_alerts()
        if escalated:
            # First, get a list of alerts that qualify.
            to_send = []
            for alert in escalated:
                # Room index higher than '0' imples escalation
                if alert["room_index"] > -1:
                    to_send.append(alert)

            # If there are some alerts that qualify, notify room.
            if to_send:
                await message.respond("Escalated alerts:")
                time.sleep(1)

                for alert in to_send:
                    await message.respond(Message(str("Escalation: {severity} {name}: {message}".format(
                        name=alert["name"],
                        severity=alert["severity"],
                        message=alert["message"]
                    ))))
            else:
                await message.respond("There are no escalated alerts")
        else:
            await message.respond("There are no escalated alerts")

    # Alias for `acknowledge`
    @match_parse('ack {uuid}')
    async def ack(self, message):
        """Alias for 'acknowledge'"""
        await self.acknowledge(message)

    @match_parse('acknowledge {uuid}')
    async def acknowledge(self, message):
        """Acknowledge a given alert. This prevents further notifications about it."""
        uuid = message.entities['uuid']['value']
        _LOGGER.info(f"SKILL: '!acknowledge' called with uuid {uuid}")

        is_found = await self.delete_by_uuid(uuid)
        if is_found:
            await message.respond("Confirmation succeeded: {}".format(uuid))
        else:
            await message.respond("No match found for this ID: {}".format(uuid))

    async def get_pending_alerts(self):
        """Return the pending alerts."""
        pending = await self.opsdroid.memory.get("pending_alerts")
        if pending is None:
            pending = []
        return pending

    async def store_alert(self, alert):
        """Store an alert into the database."""
        pending = await self.get_pending_alerts()
        pending.append(alert)
        await self.opsdroid.memory.put("pending_alerts", pending)
        _LOGGER.info(f"DB: stored alert: {alert}")
        await self.log_pending_alert_state()

    async def log_pending_alert_state(self):
        """Log the pending alerts"""
        pending = await self.get_pending_alerts()
        _LOGGER.info(f"DB: current pending alert state:")
        for alert in pending:
            _LOGGER.info(f"{alert}")

    async def delete_by_uuid(self, uuid):
        """Delete an alert by UUID from the pending list."""
        pending = await self.get_pending_alerts()
        is_found = False
        for alert in pending:
            if alert["uuid"] == uuid:
                pending.remove(alert)
                is_found = True
                _LOGGER.info(f"DB: deleted {alert}")

        await self.opsdroid.memory.put("pending_alerts", pending)
        await self.log_pending_alert_state()

        return is_found
