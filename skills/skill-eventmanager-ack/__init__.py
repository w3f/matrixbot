import uuid as uuid_pkg
import logging
import pprint
import time
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse, match_crontab, match_webhook
from aiohttp.web import Request
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)

def build_event_message(alert):
    """Build an alert notification message."""
    return str(
        "{severity} {name}: {message} \nPlease provide a acknowledgment using the following command: \"ack {uuid}\"".format(
            name=alert["name"],
            severity=alert["severity"],
            message=alert["message"],
            uuid=alert["uuid"]
        ))

def build_escalation_message(alert):
    """Build an esclation message."""
    return str(
        "ESCALATION: notifying relevant authorities about the following incident: {severity} {name}: {message}".format(
            name=alert["name"],
            severity=alert["severity"],
            message=alert["message"]
        ))

def build_escalation_occurred(alert):
    """Build an escalation message with ends up in the final escalation channel"""
    return str(
        "ESCALATION occurred: {severity} {name}: {message}".format(
            name=alert["name"],
            severity=alert["severity"],
            message=alert["message"]
        ))

class EventManagerAck(Skill):

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
                "reminder_counter": 0,
            }

            await self.store_alert(alert_context)
            await self.opsdroid.send(Message(build_event_message(alert_context)))

    #TOCHANGE every minute for testing pourposes
    @match_crontab('*/1 * * * *', timezone="Europe/Rome")
    async def crontab_show_pending(self, _):
        """Notify users about the pending alerts."""
        pending = await self.get_pending_alerts()
        if pending:
            await self.opsdroid.send(Message(text="Some confirmations still require your attention:"))
            time.sleep(1)
            for alert in pending:
                pending.remove(alert)
                # Increment counter
                alert["reminder_counter"] += 1

                if alert["reminder_counter"] == self.config.get("escalation_threshold"):
                    _LOGGER.info(f"ESCALATION: {alert}")
                    await self.store_escalation(alert)
                    await self.opsdroid.send(Message(build_escalation_message(alert)))
                else:
                    pending.append(alert)
                    await self.opsdroid.send(Message(build_event_message(alert)))

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
            await message.respond("Pending alerts:")
            time.sleep(1)
            for alert in pending:
                await self.opsdroid.send(Message(build_event_message(alert)))
        else:
            await message.respond("There are no pending alerts")

    @match_parse('escalated')
    async def escalations(self, message):
        """Respond with escalations."""
        _LOGGER.info(f"SKILL: 'escalated' called")

        escalated = await self.get_escalations()
        if escalated:
            await message.respond("Escalated alerts:")
            time.sleep(1)
            for alert in escalated:
                await self.opsdroid.send(Message(build_event_message(alert)))
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

    async def get_escalations(self):
        """Return the escalations."""
        pending = await self.opsdroid.memory.get("escalated_alerts")
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

    async def store_escalation(self, alert):
        """Store an escalation into the database."""
        # Add alert to escalation list
        escalations = await self.get_escalations()
        escalations.append(alert)
        await self.opsdroid.memory.put("escalated_alerts", escalations)
        _LOGGER.info(f"DB: stored escalation: {alert}")

        # Remove alert from pending list
        uuid = alert["uuid"]
        await self.delete_by_uuid(uuid)
        await self.log_escalation_state()

        # Notifying escalation room about this event.
        escalation_room = self.config.get("escalation_room")
        _LOGGER.info(f"Notifying room {escalation_room} about escalation")
        await self.opsdroid.send(Message(text=build_escalation_occurred(alert), target=escalation_room))

    async def log_pending_alert_state(self):
        """Log the pending alerts"""
        pending = await self.get_pending_alerts()
        _LOGGER.info(f"DB: current pending alert state:")
        for alert in pending:
            _LOGGER.info(f"{alert}")

    async def log_escalation_state(self):
        """Log the escalations."""
        escalations = await self.get_escalations()
        _LOGGER.info(f"DB: current escalation state:")
        for esc in escalations:
            _LOGGER.info(f"{esc}")

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
