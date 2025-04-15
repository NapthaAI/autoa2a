from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from common.utils.push_notification_auth import PushNotificationSenderAuth
from taskmanager import AgentTaskManager
from agent import LangGraphA2AWrapperAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10000)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="reflection_agent",
            name="Reflection Agent",
            description="This agent reflects on the user's query",
            tags=["reflection", "reasoning", "agent"],
            examples=["Example task for Reflection agent"],
        )

        agent_card = AgentCard(
            name="Reflection Agent",
            description="This agent reflects on the user's query",
            url=f"http://{host}:{port}/",
            version="0.1.0",
            defaultInputModes=LangGraphA2AWrapperAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=LangGraphA2AWrapperAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()

        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(
                agent=LangGraphA2AWrapperAgent(),
                notification_sender_auth=notification_sender_auth,
            ),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"]
        )

        logger.info(f"✅ Server running at http://{host}:{port}")
        server.start()

    except MissingAPIKeyError as e:
        logger.error(f"❌ Missing API Key: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Server startup error: {e}")
        exit(1)

if __name__ == "__main__":
    main()