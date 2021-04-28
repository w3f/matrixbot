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

class MySkill(Skill):

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
              "message": msg
            }
            await self.store_ack(toBeStored)
            await self.opsdroid.send(Message(self.build_event_message(toBeStored)))    

    #TOCHANGE very one minute for testing pourposes
    @match_crontab('*/1 * * * *', timezone="Europe/Rome")
    async def crontab_show_pending(self, event):
        pending = await self.get_pending_acks()
        if pending:
          await self.opsdroid.send(Message(text="ACK SERVICE: Some confirmations still require your attention:"))
          for p in pending:
              await self.opsdroid.send(Message(self.build_event_message(p)))  

    # @match_parse('ACK:store {toBeStored}')
    # async def store(self, message):
    #     toBeStored = message.entities['toBeStored']['value']
    #     await self.store_ack({"uuid":uuid.uuid4().hex,"value":toBeStored})
    #     await message.respond('Stored: {}'.format(toBeStored))

    @match_parse('ACK:pending')
    async def pending_acks(self, message):
        _LOGGER.info(f"SKILL: ACK pending called")
        
        pending = await self.get_pending_acks()
        await self.log_acks(pending)
        await message.respond("ACK SERVICE: Pending Acks:")
        for p in pending:
              await self.opsdroid.send(Message(self.build_event_message(p)))      

    @match_parse('ACK:confirm {uuid}')
    async def delete(self, message):
        uuid = message.entities['uuid']['value']
        _LOGGER.info(f"SKILL: ACK confirm called with uuid {uuid}")

        isFound = await self.delete_by_uuid(uuid)
        if isFound == True:
            await message.respond("ACK SERVICE: Confirmation Success: {}".format(uuid))     
        else:
            await message.respond("ACK SERVICE: No id match found for this id: {}".format(uuid))        

    async def get_pending_acks(self):
        pending_acks = await self.opsdroid.memory.get("pending_ack")
        if pending_acks is None:
          pending_acks = []
        return pending_acks  

    async def store_ack(self,toBeStored):
        acks = await self.get_pending_acks()
        acks.append(toBeStored)
        await self.opsdroid.memory.put("pending_ack", acks)
        _LOGGER.info(f"DB: Stored {toBeStored}")
        await self.log_db_state()

    async def log_db_state(self):
        pending_acks = await self.get_pending_acks()
        _LOGGER.info(f"DB: current state, pending acks:")
        for ack in pending_acks:
            _LOGGER.info(f"{ack}")    

    async def log_acks(self,acks):
        _LOGGER.info(f"SKILL: acks:")
        for ack in acks:
            _LOGGER.info(f"{ack}")         

    async def delete_by_uuid(self,uuid):
        pending_acks = await self.get_pending_acks()
        isFound = False
        for ack in pending_acks:
            if ack["uuid"] == uuid:
                pending_acks.remove(ack)
                await self.opsdroid.memory.put("pending_ack", pending_acks)
                isFound = True
                _LOGGER.info(f"DB: Deleted {ack}") 
                await self.log_db_state()
        return isFound   

    def build_event_message(self,ack):
        return str(
                "{severity} {name}: {message}. Please provide a confirmation using the following command: 'ACK:confirm {uuid}' ".format(
                    name=ack["name"],
                    severity=ack["severity"],
                    message=ack["message"],
                    uuid=ack["uuid"]
                ))                        