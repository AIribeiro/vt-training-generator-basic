# Standard Library Imports
import re
import json
import random
import hashlib
import asyncio
import csv
import uuid
from datetime import datetime, timedelta
from collections.abc import MutableMapping

# External Libraries Imports
import pandas as pd





import streamlit as st
import requests

# Azure Imports
from azure.storage.blob import BlobServiceClient
from azure.storage.fileshare import ShareServiceClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from azure.data.tables import TableServiceClient, generate_account_sas, ResourceTypes, AccountSasPermissions
from azure.core.credentials import AzureNamedKeyCredential, AzureSasCredential


# Streamlit Feedback Import
from streamlit_feedback import streamlit_feedback
from streamlit_player import st_player
# Initialize some variables
now = str(uuid.uuid4())

import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

import nltk
from nltk.tokenize import sent_tokenize

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

volvo_news= """
Welcome to a new era at Volvo Trucks, where Artificial Intelligence and Data Analytics are not just transforming our vehicles but also revolutionizing our business landscape. 

Every day, our trucks gather mountains of data, and with AI, we're turning these insights into better fleet management solutions and customer experiences. From predictive maintenance to personalized service offerings, we're leveraging data to enhance reliability and customer satisfaction. In our commercial strategies, AI helps analyze market trends and customer feedback, guiding us in developing innovative solutions that meet evolving needs. Data analytics also streamlines our supply chain, ensuring efficiency from production to delivery. 

By integrating AI and analytics into every facet of our operations, from product development to sales strategies, Volvo Trucks is not just building better vehicles, but also forging stronger connections with our customers and leading the way in a data-driven future.” 

"""




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

sentences_to_remove = ["The video should be concise, informative, and visually engaging, with a professional tone and appropriate for a corporate setting. The video should be tailored to directly address the user's request, focusing solely on delivering the essential message. The video should be no longer than 1 minute.", "<|im_end|>", "The output should be:", "The video should be clear, concise, and engaging, utilizing appropriate industry jargon and aligning with corporate scenarios.", "The video should be tailored to a corporate audience and should be clear, concise, and engaging. Ensure that the video accurately captures the user's intended meaning and aligns with Volvo Trucks' brand and values.", ".<|im_end|>", "User Input: ", "Output: ","Topic:","Script:", "Narrator:", "Voiceover:", "Topic: ","[Narrator]", "This is the video content: Narrator: ", "Video Script:", "Video Script: ", "Voiceover:", "Voiceover: ", " [Narrator] ", "[Polish Voiceover]","Narrator:", "Narrator", "Narrator: ", "Narrative:", "Narrative: ", "Narrador:", "Narrador: "]


    
    
    
    
    
 




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
Your role as an AI Video Creator is to craft informative, concise explainer text from user inputs. Focus on these key areas:

Content Fidelity: The Explainer text must accurately reflect the user's intended message, tone, and nuances. Ensure the core message is evident in the text format.
Contextual Understanding: Incorporate Volvo Trucks-specific contexts, including industry terminologies and cultural nuances. Explainer text should demonstrate a thorough understanding of the automotive and trucking industries, aligning with corporate scenarios.
Quality and Clarity: Produce clear, engaging, and straightforward Explainer text that support effective communication and decision-making in a diverse, global corporate environment.
Professionalism: Maintain professionalism in content, ensuring that the narrative, tone, and visuals align with Volvo Trucks' brand values and corporate standards.
Conciseness: Respond directly to the user's request, focusing on delivering only the essential message. Aim for brevity, with each Explainer text concisely presenting the content for quick understanding and decision-making. 
Only answer to questions that are relevant or related to the Volvo Group.
Output Requirement: Provide plain text only, without additional content or outlines, narration refences, etc. The text will be used directly for video generation, so ensure you provide me only the content, nothing else. Avoid adding works like Narrator, voiceover, video script, etc at the beginning of the text.
Refer directly to the employees, when explaining the concepts provided by the user input.

"""

def get_translation_explanation(action):
    explanations = {
        "Generate a training about AI and Analytics": "Generate a video explainer about the AI and Analytics topic suggested by the user.",
        "Generate a training about Digital Marketing": "Generate a video explainer about the Digital Marketing topic suggested by the user.",
        "Generate a training about Truck Sales": "Generate a video explainer about the Trucks Sales topic suggested by the user.",
        "Generate a training about any other topic": "Generate a video explainer about the topic suggested by the user, but related to Volvo Trucks."
        
    }
    return explanations.get(action, "Action not recognized. Please try another.")

def get_translation_prompt(action):
    prompts = {
        "Generate a training about AI and Analytics": "Generate a 1-minute video explainer about the AI and Analytics topic based on the user input: ",
        "Generate a training about Digital Marketing": "Generate a 1-minute video explainer about the Digital Marketing topic based on the user input: ",
        "Generate a training about Truck Sales": "Generate a 1-minute video explainer about the Trucks Sales topic based on the user input: ",
        "Generate a training about any other topic": "Generate a 1-minute video explainer about the topic based on the user input, that must be related to Volvo Trucks."
        
    }
    return prompts.get(action, "Topic not recognized or relevant to Volvo Trucks. Please try another.")

def generate_new_session_id():
    return str(uuid.uuid4())


content=""    
    
    
def app():
    with st.expander("How to Use This App"):
        st.write("""
            1. Select a Translation Function from the sidebar.
            2. Choose a language for translation.
            3. Enter the text you want to translate in the provided text area.
            4. Click 'Translate' to get the AI-generated translation.
            5. Provide your feedback on the translation quality.
        """)

    with st.expander("**Important Note:**"):
        st.write("""
            This application is in its prototype stage. Any information or responses generated by the AI system should be taken with a grain of caution as they may not always be accurate or up-to-date. 

            It's essential you cross-verify the AI-generated information with reliable sources or through consultation with experts in the field. 

            Additionally, be mindful of data privacy and security: DO NOT SHARE any confidential data, personal or sensitive data, or any proprietary information with the AI system that could compromise the integrity and security of our corporate data.
        """)

    technique = st.sidebar.selectbox(
        'Select the Training generation Function You Want:', 
        ["Generate a training about AI and Analytics", "Generate a training about Digital Marketing", "Generate a training about Truck Sales", "Generate a training about any other topic"]
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
    
    st.sidebar.subheader('Pick your area of interest')
    st.sidebar.write(get_translation_explanation(technique))

    
    
    
    
    
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
                "talkingAvatarStyle": "graceful-sitting",  # talking avatar style, required for prebuilt avatar, optional for custom avatar
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    user_input = st.text_area("Describe with more details as possible what the training you want to generate is about. Start for example with: Generate training explaining the value of data literacy for Volvo Trucks employees.... :", value="Generate a training explaining", key="user_input")

    if st.button('Generate the Content for the Training'):
        prompt = "According to the following ground rules: " + str(prompt_ground_rules) + str(get_translation_prompt(technique)) + user_input + f" in {language}." 
        
        

        # gets the API Key from environment variable AZURE_OPENAI_API_KEY
        client = AzureOpenAI(api_key="35fcd9150f044fdcbca33b5c3318a1f2",azure_endpoint="https://vt-generative-ai-dev.openai.azure.com/", api_version="2023-09-15-preview"
        )


        
        response = client.completions.create(model=deployment_id_4,  # Replace with your deployment ID
            #engine=deployment_id_4,  # Replace with your deployment ID
            prompt=prompt,
            temperature=0.2,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )
        content = response.choices[0].text
        content= str(response.choices[0].text.strip()) 
        
        #return content
        with st.spinner("Generating the content...It will take only 1 minute..."):
            
                    
                    cleaned_content = remove_sentences(content, sentences_to_remove)
                    
                    st.write("This is the video content: " + str(cleaned_content))
                    job_id = submit_synthesis(cleaned_content)

                    if job_id is not None:
                        with st.spinner("Generating the video...It may take some minutes...but it's worth waiting"):
                            while True:
                                status = get_synthesis(job_id)
                                if status == 'Succeeded':
                                    logger.info('batch avatar synthesis job succeeded')
                                    st.success("Video generated by Artificial Intelligence!")
                                    break
                                elif status == 'Failed':
                                    logger.error('batch avatar synthesis job failed')
                                    st.error("Video generation failed. Please try again later")
                                    break
                                else:
                                    logger.info(f'batch avatar synthesis job is still running, status [{status}]')
                                    time.sleep(5)                
                
                
                
                    
       
    
    st.sidebar.subheader('Suggested Example')
    suggested_content = {
        "Translate a Volvo Group´s public news": "Just select 1 language and click on the button 'Click here to translate' to check how the news 'Volvo Trucks’ SuperTruck 2 Exceeds Freight Efficiency Goals with Focus on Aerodynamics and Advanced Engineering' gets translated into the selected language.",
        "Translate a Sentence, Phrase, or Word": "How can Volvo's innovative technologies improve road safety and environmental sustainability?",
        "Translate a Technical Term to Another Language": "Autonomous driving features in Volvo's latest truck models.",
        "Translate an Email or Message to Another Language": "Email regarding international collaboration between Volvo's different regional offices."
    }
    st.sidebar.write(suggested_content.get(technique, ""))
  





   
if __name__ == "__main__":
    main()
    app()
    
        
    





  
