from houdini import handlers
from houdini.handlers import XTPacket
from houdini.plugins import IPlugin
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from googleapiclient import discovery
from houdini.handlers.play.moderation import moderator_ban,moderator_kick
PERSPECTIVE_API_KEY = 'yourkey' # Get yourself a key from google.
TOXICITY_FILTER = 60 # filter texts with toxicity more than 60%
API_ACTIVE = False
TOXIC_FILTER = 'TOXICITY' # use TOXICITY to filter any TOXIC message

try:   
    service = discovery.build('commentanalyzer', 'v1alpha1', developerKey=PERSPECTIVE_API_KEY)
    API_ACTIVE = True
except Exception as e:
     print(f"Unable to setup Prespective API. Error: {e}")

class SwearFilter(IPlugin):
    author = "Allinol"
    description = "Perspective API Plugin"
    version = "1"
    
    def __init__(self, server):
        super().__init__(server)
        
        
    async def ready(self):
        self.server.logger.info('PerspectiveAPI Filter Ready!')
    


    def Toxicity(self, message):
        if not API_ACTIVE:
            print("Perspective API not active. Message not filtered.")
            return 0

        try:
            analyze_request = {'comment': { 'text': message}, 'requestedAttributes': {TOXIC_FILTER: {}} }
            response = service.comments().analyze(body=analyze_request).execute()

            toxicity = round(100 * float(response['attributeScores'][TOXIC_FILTER]['summaryScore']['value']))
        
            print(f"Perspective API: Message filtered. Toxicity {toxicity}. Message {message}")

            return toxicity

        except Exception as e:
            print(f'Error, {e}')
            print("Unable to filter message via Perspective API. Message not filtered.")

            return 0



    @handlers.handler(XTPacket('m', 'sm'))
    async def handle_send_message(self, p, penguin_id: int, message: str):
        loop = asyncio.get_running_loop()
        toxic = loop.run_in_executor(None,self.Toxicity(message))
        if toxic > 60:
            await p.room.send_xt('mm', message, p.id, f=lambda px: px.moderator)
            await moderator_ban(p, p.id, comment='Inappropriate language', message=message)
            await moderator_kick(p, p.id)
        if toxic > 90:
            await moderator_ban(p, p.id, comment='Inappropriate language', message=message)
        elif toxic > 80:
            # Kick'em 
            await moderator_kick(p, p.id)
        else:
            return
