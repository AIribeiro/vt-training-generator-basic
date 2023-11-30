# Standard Library Imports
import json
import random
import hashlib
import asyncio
import csv
import uuid
import time
from datetime import datetime, timedelta
from collections.abc import MutableMapping
from PIL import Image
import numpy as np

# Natural Language Processing Imports
import nltk
from nltk.tokenize import sent_tokenize

# Data Handling Imports
import pandas as pd

# Web Framework Imports
import streamlit as st

# Networking and HTTP Requests
import requests

# Azure Cloud Services Imports
from azure.storage.blob import BlobServiceClient
from azure.storage.fileshare import ShareServiceClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from azure.data.tables import TableServiceClient
from azure.core.credentials import AzureNamedKeyCredential, AzureSasCredential

# Streamlit Extensions for Feedback and Media Playback
from streamlit_feedback import streamlit_feedback
from streamlit_player import st_player
from streamlit_image_select import image_select

# Logging and File System Utilities
import logging
import os
import sys
from pathlib import Path

# Initialize a unique identifier for the current session
now = str(uuid.uuid4())

# Download necessary NLTK data
nltk.download('punkt')


# Initialize some variables
now = str(uuid.uuid4())


# Azure Configuration
# Define the connection string for Azure Table Service
connection_string = (
    "SharedAccessSignature=sv=2021-10-04&ss=btqf&srt=sco&st=2023-11-23T15%3A37%3A11Z&se=2025-10-18T14%3A37%3A00Z"
    "&sp=rwdxftlacup&sig=h64z06wvj3ejnIuQQEH3A1SJjVfF46Hos4ctc7Ol%2Fac%3D;"
    "BlobEndpoint=https://vtgenerativeaistorage.blob.core.windows.net/;"
    "FileEndpoint=https://vtgenerativeaistorage.file.core.windows.net/;"
    "QueueEndpoint=https://vtgenerativeaistorage.queue.core.windows.net/;"
    "TableEndpoint=https://vtgenerativeaistorage.table.core.windows.net/;"
)
azure_table_service = TableServiceClient.from_connection_string(conn_str=connection_string)



def generate_new_session_id():
    return str(uuid.uuid4())

def capture_feedback():
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="[Optional] Please provide an explanation for your feedback.",
    )
    user_feedback = str(feedback)
    return user_feedback

def log_to_azure_table(user_input, technique, content, language, video_url, user_feedback, avatar_style,chat_session_id):
    """
    Log user interaction data to Azure Table.

    Args:
        user_input (str): User's input text.
        technique (str): Technique used for content generation.
        content (str): Generated content.
        language (str): Selected language.
        video_url (str): URL of the generated video.
        chat_session_id (str): Current session ID.
    """
    #now = datetime.datetime.now()  # Current time for RowKey

    # Create a dictionary to hold the new log data
    new_log_data = {
        'PartitionKey': 'LogData',
        'RowKey': str(now),
        'UserInput': user_input,
        'UsedTechnique': technique,
        'Content': content,
        'Language': language,
        'Video': video_url,
        'Feedback': user_feedback,
        'AvatarStyle': avatar_style,
        'SessionID': chat_session_id
    }

    # Get a reference to a table
    table_client = azure_table_service.get_table_client('vttraininggeneratortable')

    # Fetch all entities from the table
    entities = table_client.list_entities()

    # Organize entities by SessionID
    sessions_dict = {}
    for entity in entities:
        session_id = entity.get('SessionID')  # Use get() method to avoid KeyError
        if session_id:
            if session_id not in sessions_dict:
                sessions_dict[session_id] = []
            sessions_dict[session_id].append(entity)

    # Check if there are records with the same SessionID
    existing_records = sessions_dict.get(chat_session_id, [])
    if existing_records:
        # Merge old records with the new log data
        merged_record = {**new_log_data, 'UserInput': ' '.join([record['UserInput'] for record in existing_records] + [user_input])}
        # Insert merged record
        table_client.create_entity(entity=merged_record)
    else:
        # If no existing records with the same SessionID, simply insert the new log data
        table_client.create_entity(entity=new_log_data)

    # Move deletion check outside the existing_records block
    for entity in entities:
        # Check if the 'UserInput' or 'Content' field is " " or "None" and delete the entity if it is
        if entity.get('UserInput') in [" ", "None"] or entity.get('Content') in [" ", "None"]:
            table_client.delete_entity(entity['PartitionKey'], entity['RowKey'])
    user_input=""



# Ensure the necessary NLTK data is downloaded
nltk.download('punkt')

logging.basicConfig(stream=sys.stdout, level=logging.INFO,  # set to logging.DEBUG for verbose output
        format="[%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
logger = logging.getLogger(__name__)

# Your Speech resource key and region
# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"

SUBSCRIPTION_KEY = os.getenv("SUBSCRIPTION_KEY", '79600eb0e09540ee9cad2277f6dab051')
SERVICE_REGION = os.getenv("SERVICE_REGION", "westeurope")

NAME = "Simple avatar synthesis"
DESCRIPTION = "Simple avatar synthesis description"

# The service host suffix.
SERVICE_HOST = "customvoice.api.speech.microsoft.com"

# OpenAI Configuration
#openai.api_key = "35fcd9150f044fdcbca33b5c3318a1f2"  # Set OpenAI API key
#openai.api_type = "azure"  # Set the API type to Azure
#openai.api_base = "https://vt-generative-ai-dev.openai.azure.com/"  # Set the API endpoint
#openai.api_version = "2023-09-15-preview"  # Set the API version

#from openai import AzureOpenAI
from openai import AzureOpenAI

client = AzureOpenAI(api_key="35fcd9150f044fdcbca33b5c3318a1f2",
azure_endpoint="https://vt-generative-ai-dev.openai.azure.com/",
api_version="2023-09-15-preview")




# Deployment Configuration
deployment_id_4 = "vt-text-davinci-003"  # Set the deployment ID
deployment_id_turbo ="vt-gpt-35-turbo"




# Streamlit Page Configuration
st.set_page_config(
    page_title="Volvo Trucks' Generative AI 1-minute Training Generation",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Volvo-Iron-Mark-Black.svg/2048px-Volvo-Iron-Mark-Black.svg.png",
    layout="wide"
)

def hide_streamlit_style():
    st.markdown("""
        <style>
        .reportview-container .main footer {visibility: hidden;}    
        </style>
        """, unsafe_allow_html=True)

hide_streamlit_style()

st.markdown(f'# Volvo Trucks Generative AI 1-minute Training Generation - Prototype', unsafe_allow_html=True)
st.subheader("An Innovative Generative AI-Powered Video Generator.")
st.write("Welcome! This app is designed to support effective learning and development across different languages in the global business environment of Volvo.")


def remove_sentences(content, sentences_to_remove):
    """
    Removes specified sentences from a given text.

    Parameters:
    translation (str): The original text from which sentences need to be removed.
    sentences_to_remove (list): A list of sentences to be removed from the text.

    Returns:
    str: The cleaned text with specified sentences removed.
    """
    # Splitting the translation text into sentences
    sentences = sent_tokenize(content)

    # Removing the specified sentences
    filtered_sentences = [sentence for sentence in sentences if sentence not in sentences_to_remove]

    # Recombining the remaining sentences
    cleaned_content = ' '.join(filtered_sentences)

    return cleaned_content

sentences_to_remove = ["The video should be concise, informative, and visually engaging, with a professional tone and appropriate for a corporate setting. The video should be tailored to directly address the user's request, focusing solely on delivering the essential message. The video should be no longer than 1 minute.", "<|im_end|>", "The output should be:", "The video should be clear, concise, and engaging, utilizing appropriate industry jargon and aligning with corporate scenarios.", "The video should be tailored to a corporate audience and should be clear, concise, and engaging. Ensure that the video accurately captures the user's intended meaning and aligns with Volvo Trucks' brand and values.", ".<|im_end|>", "User Input: ", "Output: ","Topic:","Script:", "Narrator:", "Voiceover:", "Topic: ","[Narrator]", "This is the video content: Narrator: ", "Video Script:", "Video Script: ", "Voiceover:", "Voiceover: ", " [Narrator] ", "[Polish Voiceover]","Narrator:", "Narrator", "Narrator: ", "Narrative:", "Narrative: ", "Narrador:", "Narrador: ", "Resposta:", "Resposta: ", "Réponse: ", "Réponse:"]


    
    
    
    
    
 




def main():
    custom_css = f"""
        body {{
            background-image: url('https://img.freepik.com/premium-photo/concept-brainstorming-artificial-intelligence-with-blue-color-human-brain-background_121658-753.jpg');
            background-size: cover;
            background-repeat: no-repeat;
        }}
    """
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

prompt_ground_rules = """
Your Role as AI content Creator is to craft informative explainer text to be used on microtraining videos.
Before processing any user input, assess if the topic is pertinent to Volvo Trucks. If the topic is unrelated or irrelevant to our business, politely inform the user and request a more suitable topic aligned with our business context.
The text must accurately convey the user's intended message, tone, and nuances. Ensure clarity and prominence of the core message.
Incorporate specific contexts related to Volvo Trucks, including industry jargon and cultural nuances. The text should demonstrate an in-depth understanding of the commercial vehicles and trucking sectors, aligning with our corporate scenarios.
Generate clear, engaging, and straightforward text that supports effective communication and decision-making within a global corporate setting.
Uphold a professional tone throughout. Ensure the narrative and tone are in line with Volvo Trucks' brand values and standards.
Directly address the user's request, focusing on delivering only the essential message in a brief, comprehensible format.
When explaining concepts from user inputs, speak directly to Volvo Trucks' employees. Do not respond as a representative of Volvo Trucks but as an informative source. If the input is off-topic, guide the user to provide relevant content.
Provide only plain text, free from additional content or narration references. This text will be used directly in video generation, so it should be concise but complete on its own. Use varied expressions to avoid repetition of 'Volvo Trucks', such as 'we', 'us', 'our company', or 'our colleagues', when contextually appropriate.
 
"""






#user_input = user_message
user_feedback = ""
chat_session_id=""
chat_session_id_temp=""
chat_answer_temp=""
chat_question_temp=""
user_feedback_temp =""
chat_session_id_temp=""
technique=""
chat_interactions=0

content=""    
user_input=""   
avatar_style=""
get_user_feedback=""

#Default avatar style
avatar_style="graceful-standing" 


if 'video_url' not in st.session_state:
    st.session_state['video_url'] = None


if 'chat_question' not in st.session_state:
    st.session_state['chat_question'] = None

if 'chat_feedback' not in st.session_state:
    st.session_state['chat_feedback'] = None    


    
# Initialize session if not already initialized
if 'chat_session_id' not in st.session_state:
    st.session_state['chat_session_id'] = generate_new_session_id()

# Initialize the counter for tracking chatbot responses
if 'response_counter' not in st.session_state:
    st.session_state['response_counter'] = 0

# This variable will hold the chatbot's answer once the "Get Ideas" button is pressed.
chatbot_answer = None

# Initialize session state variables if they don't exist
if 'chatbot_answer' not in st.session_state:
    st.session_state['chat_answer'] = ""



def get_translation_explanation(action):
    explanations = {
        "Generate a training about AI and Analytics": "Generate a video explainer about the AI and Analytics topic suggested by the user.",
        "Generate a training about Digital Marketing": "Generate a video explainer about the Digital Marketing topic suggested by the user.",
        "Generate a training about Truck Sales": "Generate a video explainer about the Trucks Sales topic suggested by the user.",
        "Generate a training about any other topic.": "Generate a video explainer about any topic suggested by the user, but related to Volvo Trucks.",
        "Bring your own content!": "If you already have the content for the video, just copy & paste it in the text area and generate the video."
        
    }
    return explanations.get(action, "Action not recognized. Please try another.")

def get_translation_prompt(action):
    prompts = {
        "Generate a training about AI and Analytics": "Generate the text for a micro-training video explainer as an expert on Artificial Intelligence and Data Analytics, based on the following user input: ",
        "Generate a training about Digital Marketing": "Generate the text for a micro-training video explainer as an expert on Digital Marketing, based on the following user input: ",
        "Generate a training about Truck Sales": "Generate the text for a micro-training video explainer as an expert on Trucks Sales, based on the following user input: ",
        "Generate a training about any other topic.": "Generate the text for a micro-training video explainer as an expert on the topic suggested by the user on the following user input (Do not accept topics not related or not relevant to Volvo Group): ",
        "Bring your own content!": "Generate the text for a micro-training explainer video using only and exclusively the content provided by the user. "
        
    }
    return prompts.get(action, "Topic not recognized or relevant to Volvo Trucks. Please try another.")

suggested_content = {
    "Generate training about AI and Analytics": 
    "Explain the transformative impact of AI and Analytics on Volvo Trucks. For example, focus on how these technologies optimize predictive maintenance, enhance fuel efficiency, or improve safety standards. Discuss real-life applications, potential cost savings, and the future outlook of AI in the trucking industry.",

    "Generate training about Digital Marketing": 
    "Explain the strategic use of digital marketing in showcasing Volvo Trucks' innovations, including a detailed analysis of how digital marketing campaigns effectively introduce the latest range of Volvo electric trucks to a global audience. Highlight successful campaign examples, key digital channels used, and the role of data-driven marketing decisions.",

    "Generate training about Truck Sales": 
    "I need an explainer on effective sales strategies tailored for Volvo Trucks. The training must provide employees with approaches that resonate with our customers in emerging markets. Include cultural considerations in sales tactics, adapting marketing materials for local markets, and leveraging local partnerships and collaborations for broader reach.",

    "Generate training about any other topic": 
    "Choose a topic that underscores Volvo Trucks' commitment to innovation and sustainability. For example, describe Volvo Trucks' initiatives in sustainable manufacturing processes, the development of eco-friendly truck models, or the company's approach to reducing its carbon footprint and contributing to a greener future.",

    "Bring your own content!": 
    "If you already have specific content in mind, such as a recent success story, a case study specific to your department, or an insightful industry trend analysis, simply copy & paste it in the text area. This is your opportunity to create a video that highlights unique insights, experiences, or expertise relevant to Volvo Trucks."
}


def select_avatar():
    avatar_style = image_select(
    label="Select the Avatar",
    images=[
            "images/lisa-casual-sitting-thumbnail.jpg",
            "images/lisa-graceful-sitting-thumbnail.jpg",
            "images/lisa-graceful-standing-thumbnail.jpg",
            Image.open("images/lisa-technical-sitting-thumbnail.jpg"),
            np.array(Image.open("images/lisa-technical-standing-thumbnail.jpg")),
      ],
    captions=["Lisa Casual sitting", "Lisa Graceful sitting", "Lisa Graceful standing", "Lisa Technical sitting", "Lisa Technical standing"],)
    return avatar_style





    
def app():
    with st.expander("How to Use This App"):
        st.write("""
            1. Select a Training generation Function from the sidebar.
            2. Choose a language for Training.
            3. Select one of the 5 available avatars.
            4. Enter a detailed description of the training you want to create in the provided text area.If you already have the content to generate the video, simply choose the option "Bring Your Own Content" and add it to the text box.
            5. Click 'Generate the content for the training' to get the AI-generated Content.
            6. Watch the training.
            7. If the generated video is OK, download it by clicking on the link "Click here to download the video".
        """)

    with st.expander("**Important Note:**"):
        st.write("""
            This application is in its prototype stage. Any information or responses generated by the AI system should be taken with a grain of caution as they may not always be accurate or up-to-date. 

            It's essential you cross-verify the AI-generated information with reliable sources or through consultation with experts in the field. 

            Additionally, be mindful of data privacy and security: DO NOT SHARE any confidential data, personal or sensitive data, or any proprietary information with the AI system that could compromise the integrity and security of our corporate data.
            
            You can check the technical details on this AI System [here](https://volvogroup.sharepoint.com/:u:/r/sites/coll-vt-c4a-public/SitePages/Exploring-the.aspx). 
        """)

    technique = st.sidebar.selectbox(
        'Select the Training generation Function You Want:', 
        #["Generate a training about AI and Analytics", ]
        ["Generate training about AI and Analytics", "Generate training about Digital Marketing", "Generate training about Truck Sales", "Generate training about any other topic","Bring your own content!" ]
    )

    # Define the mapping of languages to TTS voice codes
    language_to_voice = {
        "English": "en-US-JennyNeural",
        "Swedish": "sv-SE-SofieNeural",
        "Brazilian Portuguese": "pt-BR-GiovannaNeural",
        "Italian": "it-IT-IsabellaNeural",
        "Spanish": "es-ES-ElviraNeural",
        "Polish": "pl-PL-AgnieszkaNeural",
        "Hindi": "hi-IN-SwaraNeural",  
        "Chinese": "zh-CN-XiaoxiaoNeural",
        "French": "fr-FR-DeniseNeural"
    }

    # Dropdown for language selection
    language = st.sidebar.radio("Select the Language for the training:", tuple(language_to_voice.keys()), index=0)

    # Assign the corresponding voice code to the variable 'voice'
    selected_voice = language_to_voice[language]
    
    
    #Select the avatar
    #select_avatar()

    # Assuming image_select is a custom function or Streamlit widget for selecting images
    use_container_width=False

    # Default selection
    default_avatar = "images/avatars/lisa-graceful-standing-thumbnail.jpg"

    # Mapping of image paths to desired avatar_style values
    avatar_mapping = {
        "images/avatars/lisa-graceful-standing-thumbnail.jpg": "graceful-standing",
        "images/avatars/lisa-casual-sitting-thumbnail.jpg": "casual-sitting",
        "images/avatars/lisa-graceful-sitting-thumbnail.jpg": "graceful-sitting",
        "images/avatars/lisa-technical-sitting-thumbnail.jpg": "technical-sitting",
        "images/avatars/lisa-technical-standing-thumbnail.jpg": "technical-standing"
    }

    # Initialize avatar_style_selection with the default value
    avatar_style_selection = default_avatar

    # User selects an avatar
    selected_avatar = image_select(
        label="Select the Avatar you want to use on your video training:",
        images=[
            "images/avatars/lisa-graceful-standing-thumbnail.jpg",
            "images/avatars/lisa-casual-sitting-thumbnail.jpg",
            "images/avatars/lisa-graceful-sitting-thumbnail.jpg",
            "images/avatars/lisa-technical-sitting-thumbnail.jpg",
            "images/avatars/lisa-technical-standing-thumbnail.jpg",
        ],
        captions=["Graceful standing","Casual sitting", "Graceful sitting", "Technical sitting", "Technical standing"],
    )

    # Update avatar_style_selection if the user makes a choice
    if selected_avatar:
        avatar_style_selection = selected_avatar

    # Assigning the corresponding value to avatar_style based on the user's selection
    avatar_style = avatar_mapping.get(avatar_style_selection)

    #st.write("Selected avatar style: " + str(avatar_style))




    
    
    
    
    st.sidebar.subheader('Pick your area of interest')
    st.sidebar.write(get_translation_explanation(technique)) 
    st.sidebar.subheader('Copy & Paste the example below in the text area to get started.')
    
    st.sidebar.write(suggested_content.get(technique, ""))

    
    
    
    
    
    #Synthesis functions
    
    
    
    
    def submit_synthesis(content):
        url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar'
        header = {
            'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
            'Content-Type': 'application/json'
        }

        payload = {
            'displayName': NAME,
            'description': DESCRIPTION,
            "textType": "PlainText",
            'synthesisConfig': {
                "voice": selected_voice,
            },
            # Replace with your custom voice name and deployment ID if you want to use custom voice.
            # Multiple voices are supported, the mixture of custom voices and platform voices is allowed.
            # Invalid voice name or deployment ID will be rejected.
            'customVoices': {
                # "YOUR_CUSTOM_VOICE_NAME": "YOUR_CUSTOM_VOICE_ID"
            },
            "inputs": [
                {
                    "text": content,
                },
            ],
            "properties": {
                "customized": False, # set to True if you want to use customized avatar
                "talkingAvatarCharacter": "lisa",  # talking avatar character
                "talkingAvatarStyle": avatar_style,  # talking avatar style, required for prebuilt avatar, optional for custom avatar
                "videoFormat": "mp4",  # mp4 or webm, webm is required for transparent background
                "videoCodec": "h264",  # hevc, h264 or vp9, vp9 is required for transparent background; default is hevc
                "subtitleType": "soft_embedded",
                "backgroundColor": "white",
            }
        }

        response = requests.post(url, json.dumps(payload), headers=header)
        if response.status_code < 400:
            logger.info('Batch avatar synthesis job submitted successfully')
            logger.info(f'Job ID: {response.json()["id"]}')
            return response.json()["id"]
        else:
            logger.error(f'Failed to submit batch avatar synthesis job: {response.text}')


    def get_synthesis(job_id):
        url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar/{job_id}'
        header = {
            'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY
        }
        response = requests.get(url, headers=header)
        if response.status_code < 400:
            logger.debug('Get batch synthesis job successfully')
            logger.debug(response.json())
            if response.json()['status'] == 'Succeeded':
                download_url = response.json()["outputs"]["result"]
                logger.info(f'Batch synthesis job succeeded, download URL: {download_url}')
                st.session_state['video_url']= download_url
                
                st.success('Batch synthesis job succeeded!')
                #video_file = open(download_url, 'rb')
                #video_bytes = video_file.read()
                
                
                
                #video logo
                
                
                
                
                
                
                

                st.video(download_url)

                #st_player(download_url)
                st.markdown(f'[Click here to download the video]({download_url})', unsafe_allow_html=True)
            return response.json()['status']
        else:
            logger.error(f'Failed to get batch synthesis job: {response.text}')


    def list_synthesis_jobs(skip: int = 0, top: int = 100):
        """List all batch synthesis jobs in the subscription"""
        url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar?skip={skip}&top={top}'
        header = {
            'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY
        }
        response = requests.get(url, headers=header)
        if response.status_code < 400:
            logger.info(f'List batch synthesis jobs successfully, got {len(response.json()["values"])} jobs')
            logger.info(response.json())
        else:
            logger.error(f'Failed to list batch synthesis jobs: {response.text}')

    
    
    
    
    
    
    
    #End of synthesis functions
    
    
    
    
    
    
    
    
    
    
    
    
#the game starts here!    
    # Initializing session state variables if they don't exist
    if 'technique' not in st.session_state:
        st.session_state['technique'] = ""
    if 'language' not in st.session_state:
        st.session_state['language'] = ""
    if 'chat_answer' not in st.session_state:
        st.session_state['chat_answer'] = ""
    if 'video_url' not in st.session_state:
        st.session_state['video_url'] = ""

    # Setting the technique and language based on user selection
    st.session_state['technique'] = technique
    st.session_state['language'] = language

    # User input for training content
    user_input = st.text_area("Describe with more details as possible what the training you want to generate is about. Before proceed, ensure that you selected the right function on the sidebar (Analytics, Marketing, Truck Sales, Any content or your own content). REMEMBER: Only content relevant to Volvo Trucks will be processed. You can make it relevant for Volvo Trucks by mentioning for example, expressions like 'for volvo trucks employees', ' how can volvo trucks employees...', etc. ", value="", key="user_input")

    # Flag to track if the input is valid
    is_input_valid = False

    # Automatically check the length of the input in terms of approximate tokens
    if user_input:
        approx_tokens = len(user_input) / 4  # Rough estimation of tokens
        if approx_tokens < 50:
            st.error("Please provide more details in your input. The description should be at least 200 characters long for better results.")
        elif approx_tokens > 2000:
            st.error("Your input is too long. Please limit the description to 8000 characters or less.")
        else:
            is_input_valid = True  # Input is valid only if it's within the c




    if st.button('Generate the Content for the Training')and is_input_valid:
        if technique == "Bring your own content!":
            prompt = "Generate a new text as more similar as possible to the following user input: " + user_input + f". Your response must be in the following language: {language}. Ensure it fully respects the following ground rules: " + str(prompt_ground_rules) 
            client = AzureOpenAI(api_key="35fcd9150f044fdcbca33b5c3318a1f2", azure_endpoint="https://vt-generative-ai-dev.openai.azure.com/", api_version="2023-09-15-preview")
            response = client.completions.create(model=deployment_id_4, prompt=prompt, temperature=0.2, max_tokens=2000, top_p=1, frequency_penalty=0, presence_penalty=0, stop=None)
            content = str(response.choices[0].text.strip())
            st.session_state['chat_answer']= content
            chat_session_id = generate_new_session_id()
        else:
            prompt = "" + str(get_translation_prompt(technique)) + user_input + f" in {language}.Ensuring full compliance to the following ground rules: " + str(prompt_ground_rules)
            client = AzureOpenAI(api_key="35fcd9150f044fdcbca33b5c3318a1f2", azure_endpoint="https://vt-generative-ai-dev.openai.azure.com/", api_version="2023-09-15-preview")
            response = client.completions.create(model=deployment_id_4, prompt=prompt, temperature=0.2, max_tokens=2000, top_p=1, frequency_penalty=0, presence_penalty=0, stop=None)
            content = str(response.choices[0].text.strip())
            st.session_state['chat_answer']= content
            
        #Generate a new sessionID
        chat_session_id = generate_new_session_id()
        
        # Display the generated content and ask for user confirmation
        cleaned_content = remove_sentences(content, sentences_to_remove)
        st.session_state['chat_answer'] = cleaned_content
        st.write("This is the content to be used to generate the video: " + str(st.session_state['chat_answer']) + ". Note: In certain cases, AI may apply some changes to the content to align it to the objectives of the application.")
        
        job_id = submit_synthesis(st.session_state['chat_answer'] if st.session_state['technique'] != "Bring your own content!" else st.session_state['user_input'])
        if job_id is not None:
                with st.spinner("Generating the video...It may take some minutes...but it's worth waiting"):
                    while True:
                        status = get_synthesis(job_id)
                        if status == 'Succeeded':
                            logger.info('batch avatar synthesis job succeeded')
                            st.success("Video generated by Artificial Intelligence!")
                            video_url = st.session_state['video_url']
                            #user_feedback = "None"  # Placeholder for feedback capturing
                            content = st.session_state['chat_answer']
                            
                            #Feedback
                            user_feedback = st.text_input("Say something")
                            
                            #Log saving
                            log_to_azure_table(st.session_state['user_input'], st.session_state['technique'], content, st.session_state['language'], video_url, user_feedback, avatar_style, chat_session_id)
                            if st.button('Send your feedback'):
                                st.write("this is your feedback: " +str(user_feedback))
                                log_to_azure_table(st.session_state['user_input'], st.session_state['technique'], content, st.session_state['language'], video_url, user_feedback, avatar_style, chat_session_id)
                                break
                        elif status == 'Failed':
                            logger.error('batch avatar synthesis job failed')
                            st.error("Video generation failed. Please try again later")
                            break
                        else:
                            logger.info(f'batch avatar synthesis job is still running, status [{status}]')
                            time.sleep(5)    

    # ... [rest of the code] ...
                
                
                
                
                    
       
    
    
   
  



   

    user_input=""   
if __name__ == "__main__":
    main()
    app()
    user_input=""
    
    





  
