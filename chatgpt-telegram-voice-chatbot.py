# Import the necessary libraries and modules
from telegram.utils.request import Request
from telegram import Bot
from telegram.ext import Updater, MessageHandler, Filters
import telegram
import openai
from moviepy.editor import AudioFileClip
from elevenlabs import generate, set_api_key, stream
from langdetect import detect
import os

# Set the API key for Eleven Labs (Text-to-Speech service)
set_api_key("YOUR_ELEVEN_LABS_API_KEY_HERE")

# Set the API key for OpenAI (Used for GPT-3 and Whisper ASR)
openai.api_key = "YOUR_OPENAI_API_KEY_HERE"

# Set the API token for Telegram bot
TELEGRAM_API_TOKEN = "YOUR_TELEGRAM_API_TOKEN_HERE"

# Define a helper function to check if the input text is in English
def language_is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return True  # default to English if detection fails

# Create a Request object with a connection pool size of 8
request = Request(con_pool_size=8)

# Create a Bot object with the API token and the request object
bot = Bot(TELEGRAM_API_TOKEN, request=request)

# Create an Updater object with the bot
updater = Updater(bot=bot, use_context=True)

# Define a list to store the messages
messages = [
    {
        "role": "system",
        "content": """Act as an expert in all subject matters, providing concise, accurate, and insightful
        answers to any questions or concerns raised. Ensure your responses are clear, precise, and in English.
        Maintain an informative and helpful tone in your responses, demonstrating your expertise and understanding
        of a wide range of topics. Ensure that you only respond back with answers that you are fully confident in.
        Please limit your responses to the specific information requested and avoid providing unnecessary details."""
    }
]

# Define a function to handle text messages
def text_message(update, context):
    # Add the received message to the messages list
    messages.append({"role": "user", "content": update.message.text})

    # Generate a response using the OpenAI GPT-3 model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ChatGPT_reply = response["choices"][0]["message"]["content"]

    # Send the generated response back to the user as a text message
    update.message.reply_text(text=f"*[ChatGPTCrafters]:* {ChatGPT_reply}", parse_mode=telegram.ParseMode.MARKDOWN)

    # Generate an audio version of the response using Eleven Labs API
    audio = generate(
        text=ChatGPT_reply,
        voice= "Rachel",
        model="eleven_multilingual_v1"
    )

    # Save the audio file
    with open("ChatGPT_reply.mp3", "wb") as f:
        f.write(audio)

    # Send the audio file as a voice message
    with open("ChatGPT_reply.mp3", "rb") as audio_file:
        context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)

    # Add the generated response to the messages list
    messages.append({"role": "assistant", "content": ChatGPT_reply})

# Define a function to handle voice messages
def voice_message(update, context):
    # Inform the user that the bot has received the voice message and is processing it
    update.message.reply_text("I've received a voice message! Please give me a second to respond :)")

    # Download the voice message
    voice_file = context.bot.getFile(update.message.voice.file_id)
    voice_file.download("voice_message.ogg")

    # Convert the ogg file to mp3
    audio_clip = AudioFileClip("voice_message.ogg")
    audio_clip.write_audiofile("voice_message.mp3")

    # Open the mp3 file and transcribe it using OpenAI's Whisper ASR system
    with open("voice_message.mp3", "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file).text

    # Send the transcript back to the user
    update.message.reply_text(text=f"*[You]:* _{transcript}_", parse_mode=telegram.ParseMode.MARKDOWN)

    # Add the transcript to the messages list
    messages.append({"role": "user", "content": transcript})

    # Generate a response using the OpenAI GPT-3 model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ChatGPT_reply = response["choices"][0]["message"]["content"]

    # Send the generated response back to the user as a text message
    update.message.reply_text(text=f"*[ChatGPTCrafters]:* {ChatGPT_reply}", parse_mode=telegram.ParseMode.MARKDOWN)

    # Generate an audio version of the response using Eleven Labs API
    audio = generate(
        text=ChatGPT_reply,
        voice="Rachel",
        model="eleven_multilingual_v1"  # Use the multilingual model
    )

    # Save the audio file
    with open("ChatGPT_reply.mp3", "wb") as f:
        f.write(audio)

    # Send the audio file as a voice message
    with open("ChatGPT_reply.mp3", "rb") as audio_file:
        context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)

    # Add the generated response to the messages list
    messages.append({"role": "assistant", "content": ChatGPT_reply})

# Create an Updater object
updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Add handlers for text and voice messages
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text_message))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_message))

# Start the bot and set it to idle
updater.start_polling()
updater.idle()

