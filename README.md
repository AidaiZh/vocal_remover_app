**app_youtube.py** is a Python script designed to process YouTube videos by removing vocals from the audio tracks. It leverages the vocal_remover model to isolate and extract instrumental tracks from the given video files. This script automates the process, making it easy to convert YouTube videos into karaoke versions or instrumental tracks for various uses.


## How to use
1. Clone this model repository
```
git clone https://github.com/tsurumeso/vocal-remover.git
```
The script provides two API endpoints:

1. Audio File Endpoint: Processes an audio file directly to remove vocals.
2. YouTube Link Endpoint: Takes a YouTube link, downloads the video, extracts the audio, and then removes the vocals.
   
To access YouTube, a www.youtube.com_cookies.txt file is required. You can create this cookies file using a browser extension:

Install the Extension:

Go to the Chrome Web Store (or your browser's equivalent) and search for "EditThisCookie" or any cookie editor extension.
Install the extension.
Access YouTube:

Open your browser and navigate to www.youtube.com.
Make sure you are logged in to your YouTube account if required.
Export Cookies:

Click on the extension icon (usually found near the browser's address bar).
In the cookie editor interface, look for an option to export or download cookies.
Select the option to export cookies, and choose the format suitable for yt-dlp (Netscape HTTP Cookie File format).
Save the File:

Save the exported cookies file as www.youtube.com_cookies.txt on your computer.
2. To run the script, use the following command:
```
python app_youtube.py
```
