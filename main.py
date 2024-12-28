import os

from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from flask import Flask, request
from langchain_openai import ChatOpenAI

load_dotenv()

app = Flask(__name__)

# @app.route('/send-message', methods=['POST'])


@app.route('/messages-upsert', methods=['POST'])
def send_message():
    print("Data received from Webhook is (Send Message): ", request.json)
    request_json = request.json
    event = request_json['event']
    data = request_json['data']
    conversation = data['message']['conversation']
    remoteJid = data['key']['remoteJid']
    response = ''

    if (event == 'messages.upsert'):
        llm = ChatOpenAI(
            model='llama3:latest',
            base_url='http://localhost:11434/v1'
        )

        response = llm.invoke(conversation)
        # print(response.content)
        send_text(remoteJid, response.content)

    return 'OK'


def send_text(number, text):
    evolution_client = EvolutionClient(
        base_url=os.getenv('EVO_API_BASE_URL'),
        api_token=os.getenv('EVO_API_TOKEN')
    )

    # print(evolution_client.instances.fetch_instances())

    crewai_instance_id = 'CrewAi'
    crewai_instance_token = '7E7226AD2182-4971-A051-C4A0D775B823'

    text_message = TextMessage(
        number=number,
        text=text
    )

    response = evolution_client.messages.send_text(
        crewai_instance_id, text_message, crewai_instance_token)

    print(response)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
