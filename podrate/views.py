from django.conf import settings
from django.shortcuts import render
from django.views.generic.base import TemplateView

import boto3
import json
import os
import time
import urllib.request


from .forms import PodcastUrlForm


def index(request):
    if request.method == "POST":
        form = PodcastUrlForm(request.POST)

        if form.is_valid():
            timestamp = form.cleaned_data['timestamp']
            podcast_filename = f"podcast_{timestamp}.mp3"

            # Upload file to S3
            s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            with open(podcast_filename, 'rb') as data:
                s3.Bucket('podrate').put_object(Key=podcast_filename, Body=data)

            # Transcribe
            transcribe_client = boto3.client('transcribe', region_name="us-east-2",
                                             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            media_file_uri = f"s3://{settings.S3_BUCKET_NAME}/{podcast_filename}"
            toxic_levels = transcribe_file(f"transcribe-job-{timestamp}", media_file_uri, transcribe_client)

            # Delete locally created file
            os.remove(podcast_filename)

            return render(request, 'podcast_detail.html', context=toxic_levels)
    else:
        form = PodcastUrlForm()

    return render(request, "homepage_form.html", {"form": form})

def transcribe_file(job_name, media_file_uri, transcribe_client):
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_file_uri},
        MediaFormat="wav",
        LanguageCode="en-US",
        ToxicityDetection=[{'ToxicityCategories': ['ALL',]},]
    )

    max_tries = 60
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        if job_status in ["COMPLETED", "FAILED"]:
            print(f"Job {job_name} is {job_status}.")
            if job_status == "COMPLETED":
                print(f"Transcript uri is:")
                print(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
                return parse_transcribe_json(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(1)

def parse_transcribe_json(json_uri):
    with urllib.request.urlopen(json_uri) as url:
        data = json.load(url)

    if data["results"]["toxicity_detection"]:
        toxicity, profanity, hate_speech, sexual, insult, violence_or_threat, graphic, harassment_or_abuse = 0, 0, 0, 0, 0, 0, 0, 0
        for segment in data["results"]["toxicity_detection"]:
            toxicity += segment["toxicity"]
            profanity += segment["categories"]["profanity"]
            hate_speech += segment["categories"]["hate_speech"]
            sexual += segment["categories"]["sexual"]
            insult += segment["categories"]["insult"]
            violence_or_threat += segment["categories"]["violence_or_threat"]
            graphic += segment["categories"]["graphic"]
            harassment_or_abuse += segment["categories"]["harassment_or_abuse"]

        segments = len(data["results"]["toxicity_detection"])
        toxic_levels = {
            "toxicity_rating": round(toxicity/segments, 2),
            "profanity_rating": round(profanity/segments, 2),
            "hate_speech_rating": round(hate_speech/segments, 2),
            "sexual_rating": round(sexual/segments, 2),
            "insult_rating": round(insult/segments, 2),
            "violence_or_threat_rating": round(violence_or_threat/segments, 2),
            "graphic_rating": round(graphic/segments, 2),
            "harassment_or_abuse_rating": round(harassment_or_abuse/segments, 2)
        }
    else:
        toxic_levels = {
            "toxicity_rating": 0,
            "profanity_rating": 0,
            "hate_speech_rating": 0,
            "sexual_rating": 0,
            "insult_rating": 0,
            "violence_or_threat_rating": 0,
            "graphic_rating": 0,
            "harassment_or_abuse_rating": 0
        }

    # Make toxicity rating readable
    toxic_levels["general_toxicity_rating"] = get_rating(toxic_levels["toxicity_rating"])
    return toxic_levels

def get_rating(toxic_level):
    if 0 <= toxic_level < 0.1:
        return "G"
    elif 0.1 <= toxic_level < 0.3:
        return "PG"
    elif 0.3 <= toxic_level < 0.5:
        return "PG-13"
    elif 0.5 <= toxic_level < 0.8:
        return "R"
    elif 0.8 <= toxic_level < 1:
        return "NC-17"
    else:
        return "error"


class AboutMeView(TemplateView):
    template_name = "about_me.html"