from houdini import handlers
from houdini.handlers import XTPacket
from houdini.plugins import IPlugin
import asyncio
from houdini.handlers.play.moderation import moderator_ban,moderator_kick
PERSPECTIVE_API_KEY = 'yourkey' # Get yourself a key from google.
TOXICITY_FILTER = 60 # filter texts with toxicity more than 60%
API_ACTIVE = True # Turn Filter on or off
TOXIC_FILTER = 'TOXICITY' # use TOXICITY to filter any TOXIC message

class SwearFilter(IPlugin):
    author = "Allinol"
    description = "Perspective API Plugin"
    version = "1"
    
    def __init__(self, server):
        super().__init__(server)
        
        
    async def ready(self):
        self.server.logger.info('PerspectiveAPI Filter Ready!')
        
    async def Toxicity(self, message):
        if not API_ACTIVE:
            self.server.logger.info("Perspective API not active. Message not filtered.")
            return 0

        try:
            analyze_request = {
              'comment': {
                'text': message
              },
              'requestedAttributes': {
                TOXIC_FILTER: {}
              },
              'languages': 'en' #english is the default language you can change this to french(fr), spanish(es), german(de) , portuguese(pt) and italy(it)
            }
            async with aiohttp.ClientSession() as session:
              async with session.post(f 'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}', json = analyze_request) as resp:
                response = await resp.json()
                toxicity = round(100 * float(response['attributeScores'][TOXIC_FILTER]['summaryScore']['value']))

                self.server.logger.info(f " Toxicity {toxicity}. Message {message}")

                return toxicity

        except Exception as e:
            self.server.logger.info(f'Error, {e}')
            self.server.logger.info("Unable to filter message via Perspective API. Message not filtered.")

            return 0



    @handlers.handler(XTPacket('m', 'sm'))
    async def handle_send_message(self, p, penguin_id: int, message: str):
        toxic = await self.Toxicity(message)
        if toxic > 60:
            await p.room.send_xt('mm', message, p.id, f=lambda px: px.moderator)
            await moderator_ban(p, p.id, comment='Inappropriate language', message=message)
            await p.close()
        if toxic > 90:
            await moderator_ban(p, p.id, comment='Inappropriate language', message=message)
            await p.close()
        elif toxic > 80:
            # Kick'em 
            await moderator_kick(p, p.id)
        else:
            return
