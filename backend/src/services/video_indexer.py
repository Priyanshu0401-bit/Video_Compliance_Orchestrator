'''
Connector : connects to Azure Video Indexer
'''

import os
import time
import logging
import requests
import yt_dlp
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("video_indexer")

class VideoIndexerService:
    def __init__(self):
        self.account_id = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.resource_group = os.getenv("AZURE_VI_RESOURCE_GROUP")
        self.subscription_id = os.getenv("AZURE_VI_SUBSCRIPTION_ID")
        self.vi_name = os.getenv("AZURE_VI_NAME")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.credential = DefaultAzureCredential()

    def get_access_token(self):
        '''
        Generates an ARM Access Token
        '''
        try:
            token_object = self.credential.get_token("https://management.azure.com/.default")
            return token_object.token           
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def get_account_token(self,arm_access_token):
        '''
        Exchanges the arm token for video indexer account team
        '''

        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2024-01-01"
        )
        headers = {"Authorization" : f"Bearer {arm_access_token}"}
        payload = {
            "permission" : "Contributor",
            "scope":"Account"
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception("Failed to get account token")
        return response.json().get("accessToken")

    #download youtube video
    def download_youtube_video(self, url, output_path = "temp_video.mp4"):
        '''
        Downloads youtube video to local file
        '''
        logger.info(f"Downloading yt video: {url}")

        ydl_opt = {
            "format" : 'best[ext=mp4]',
            'outtmpl': output_path,
            'quiet' : True,
            'overwrite': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opt) as ydl:
                ydl.download([url])
            logger.info(f"video is downloaded at {output_path}")
            return output_path
        except Exception as e:
            raise Exception(f"Failed to download youtube video: {e}")
            

    #upload video to azure VI
    def upload_video(self,video_path,video_name):
        arm_token = self.get_access_token()
        vi_token = self.get_account_token(arm_token)

        api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"

        params = {
            "accessToken" : vi_token,
            "name" : video_name,
            "description" : "video from compliance tool",
            "privacy": "Private",
            "indexingPreset": "Default"
        } 

        logger.info(f"Uploading the file {video_path} to VI")

        #open file in binary and stream to azure
        with open(video_path,'rb') as video_file:
            files = {'file':video_file}
            response = requests.post(api_url, params=params, files=files)

        if response.status_code != 200:
            raise Exception(f"Failed to upload video : {response.text}")

    def wait_for_processing(self, video_id):
        logger.info(f"Wating for {video_id} to process....")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)

            url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
            params = {"accessToken" : vi_token}
            response = requests.get(url, params=params)
            data = response.json()

            state = data.get('state')
            if state == "Processed":
                return data
            elif state == "Failed":
                raise Exception("Failed Video Indexing i azure")
            elif state == "Quarantined":
                raise Exception("Video quarantined - violates content policy")
            logger.info(f"Current statu:s {state}, waiting 30s")
            time.sleep(30)


    def extract_data(self,vi_json):
        'parses the json into our state format'

        transcript_lines = []
        for v in vi_json.get("videos",[]):
            for insight in v.get("insights",{}).get("transcript",[]):
                transcript_lines.append(insight.get("text"))

        ocr_lines=[]
        for v in vi_json.get("videos",[]):
            for ocr in v.get("insights",{}).get("ocr",{}):
                ocr_lines.append(ocr.get("text"))
        return{
            "transcript": " ".join(transcript_lines),
            "ocr_texts" : ocr_lines,
            "video_metadata" : {
                "duration" : vi_json.get("summarizedInsights",{}).get("duration"),
                "platform" : "youtube"
            }
        }
            
