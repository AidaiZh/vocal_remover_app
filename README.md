**app_youtube.py** is a Python script designed to process YouTube videos by removing vocals from the audio tracks. It leverages the vocal_remover model to isolate and extract instrumental tracks from the given video files. This script automates the process, making it easy to convert YouTube videos into karaoke versions or instrumental tracks for various uses.


## How to use
1. Clone this model repository
```
git clone https://github.com/tsurumeso/vocal-remover.git
```
The script provides two API endpoints:

Audio File Endpoint: Processes an audio file directly to remove vocals.
YouTube Link Endpoint: Takes a YouTube link, downloads the video, extracts the audio, and then removes the vocals.

2. To run the script, use the following command:
```
python app_youtube.py
```
