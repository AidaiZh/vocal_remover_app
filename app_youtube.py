
from flask import Flask, request, jsonify, send_file, make_response
import os
import io
import zipfile
from inference_changed import MainProcessor
from pydub import AudioSegment
import subprocess
from moviepy.editor import *

app = Flask(__name__)

def download_youtube_audio(video_url, cookies_path, output_path):
    
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        command = [
            "yt-dlp",
            "--cookies", cookies_path,
            "--output", os.path.join(output_path, "temp_video.webm"),
            video_url
        ]
        subprocess.run(command)

        video_clip = AudioFileClip(os.path.join(output_path, "temp_video.webm"))
        audio_file_path = os.path.join(output_path, "downloaded_audio.mp3")
        video_clip.write_audiofile(audio_file_path, codec='libmp3lame')
        print("1",audio_file_path)
        os.remove(os.path.join(output_path, "temp_video.webm"))
        print("2",audio_file_path)
        return audio_file_path

#    except Exception as e:
#        print("Error during download and conversion:", str(e))
#        return None


@app.route('/separate_audio', methods=['POST'])
def separate_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file:
        # Save the audio file temporarily
        filename = 'temp_audio.wav'
        file.save(filename)
        
        
        MainProcessor.mainu(filename)
        
        # Construct filenames for separated audio files
        instruments_filename = '{}_Instruments.wav'.format(os.path.splitext(filename)[0])
        vocals_filename = '{}_Vocals.wav'.format(os.path.splitext(filename)[0])
        
        # Load separated audio files and apply compression
        instruments_audio = AudioSegment.from_file(instruments_filename)
        vocals_audio = AudioSegment.from_file(vocals_filename)

        # Apply compression (example: reduce bitrate to 128 kbps)
        compressed_instruments_audio = instruments_audio.set_frame_rate(44100).set_channels(2).export(format="wav", bitrate="128k")
        compressed_vocals_audio = vocals_audio.set_frame_rate(44100).set_channels(2).export(format="wav", bitrate="128k")

        # Read the content of compressed audio files into strings
        compressed_instruments_audio_content = compressed_instruments_audio.read()
        compressed_vocals_audio_content = compressed_vocals_audio.read()

        # Create response object
        response = make_response()
        response.headers["Content-Disposition"] = "attachment; filename=separated_files.zip"
        response.headers["Content-type"] = "application/zip"

        # Create in-memory buffer for ZIP file
        with io.BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                # Add compressed separated audio files to the ZIP archive
                zip_file.writestr('instruments.wav', compressed_instruments_audio_content)
                zip_file.writestr('vocals.wav', compressed_vocals_audio_content)

            response.data = zip_buffer.getvalue()

        return response
    

@app.route('/youtube', methods=['POST'])
def youtube_parse():
    if 'youtube' not in request.form:
        return jsonify({'error': 'No file part'})
    
    youtube_url = request.form['youtube']
    
    
    if youtube_url:
        output_path = r"/Users/aidaizhusup/vocal/vocal-remover"  # Path to save audio file
        cookies_path = r'/Users/aidaizhusup/vocal/vocal-remover/www.youtube.com_cookies.txt'
        file_path = download_youtube_audio(youtube_url,cookies_path,output_path)
        print("TALGAT",file_path)
#
        
        MainProcessor.mainu(file_path)
        
        # Construct filenames for separated audio files
        instruments_filename = '{}_Instruments.wav'.format(os.path.splitext(file_path)[0])
        vocals_filename = '{}_Vocals.wav'.format(os.path.splitext(file_path)[0])
        
        # Load separated audio files and apply compression
        instruments_audio = AudioSegment.from_file(instruments_filename)
        vocals_audio = AudioSegment.from_file(vocals_filename)

        # Apply compression (example: reduce bitrate to 128 kbps)
        compressed_instruments_audio = instruments_audio.set_frame_rate(44100).set_channels(2).export(format="wav", bitrate="128k")
        compressed_vocals_audio = vocals_audio.set_frame_rate(44100).set_channels(2).export(format="wav", bitrate="128k")

        # Read the content of compressed audio files into strings
        compressed_instruments_audio_content = compressed_instruments_audio.read()
        compressed_vocals_audio_content = compressed_vocals_audio.read()

        # Create response object
        response = make_response()
        response.headers["Content-Disposition"] = "attachment; filename=separated_files.zip"
        response.headers["Content-type"] = "application/zip"

        # Create in-memory buffer for ZIP file
        with io.BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                # Add compressed separated audio files to the ZIP archive
                zip_file.writestr('instruments.wav', compressed_instruments_audio_content)
                zip_file.writestr('vocals.wav', compressed_vocals_audio_content)

            response.data = zip_buffer.getvalue()

        return response
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6463,debug=True)
   
