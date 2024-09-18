from django import forms
from django.core.exceptions import ValidationError


import os
import requests
import time


class PodcastUrlForm(forms.Form):
    podcast_url = forms.CharField(label="Podcast URL", widget=forms.Textarea())

    def clean(self):
        cleaned_data = super(PodcastUrlForm, self).clean()
        podcast_url = cleaned_data['podcast_url']
        timestamp = round(time.time())
        podcast_filename = f"podcast_{timestamp}.mp3"

        download = requests.get(podcast_url)
        with open(podcast_filename, 'wb') as f:
            f.write(download.content)

        # Reject if the size is too big
        size_limit = 80 * 1024 * 1024 * 80  # 80MB
        file_size = os.path.getsize(podcast_filename)
        if file_size > size_limit:
            raise ValidationError("File size is too big.")

        cleaned_data.update({"timestamp": timestamp})
        return self.cleaned_data