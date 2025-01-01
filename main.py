import base64
import os
import uuid
import wave

import soundfile
from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from flask import Flask, request
from groq import Groq
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
    message_type = data['messageType']
    message = data['message']
    key = data['key']
    remote_jid = key['remoteJid']

    if 'conversation' in message:
        conversation = message['conversation']

    if 'base64' in message:
        audio_base64 = message['base64']

    response = ''

    if (event == 'messages.upsert'):
        llm = ChatOpenAI(
            model='llama3:latest',
            base_url='http://localhost:11434/v1'
        )

        if message_type == 'conversation':
            response = llm.invoke(conversation)
            # print(response.content)
            send_text(remote_jid, response.content)
        elif message_type == 'audioMessage':
            # print(audio_base64)
            audio_dir = 'audios'
            if not os.path.exists(audio_dir):
                os.mkdir(audio_dir)
            temp_audio_name = f'{uuid.uuid4()}.wav'
            full_audio_name = f'{audio_dir}/{temp_audio_name}'

            with open(full_audio_name, "wb") as file:
                decode_string = base64.b64decode(audio_base64)
                file.write(decode_string)

            data, samplerate = soundfile.read(full_audio_name)
            soundfile.write(full_audio_name, data, samplerate)

            pwd = os.path.dirname(__file__)
            audio_file = os.path.join(pwd, audio_dir, temp_audio_name)

            groq_client = Groq(
                api_key=os.getenv('GROQ_API_KEY')
            )

            with open(audio_file, "rb") as file:
                # Create a transcription of the audio file
                transcription = groq_client.audio.transcriptions.create(
                    file=(audio_file, file.read()),  # Required audio file
                    model="whisper-large-v3-turbo",  # Required model to use for transcription
                    # prompt="Specify context or spelling",  # Optional
                    response_format="json",  # Optional
                    language="br",  # Optional
                    temperature=0.0  # Optional
                )

                conversation = transcription.text
                print(conversation)
                response = llm.invoke(conversation)
                send_text(remote_jid, response.content)

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
