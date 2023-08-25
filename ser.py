from flask import Flask, render_template, request, redirect, url_for, send_file
from youtube_transcript_api import YouTubeTranscriptApi
from gtts import gTTS
from gtts.lang import tts_langs
from googletrans import Translator
from pydub import AudioSegment
import numpy as np
import os
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip, clips_array

app = Flask(__name__)
def generate_audio(text, lang, duration):
    # Generate audio using gTTS
    tts = gTTS(text=text, lang=lang, slow=True)
    tts.save("../temp_output.mp3")
    print()
    # Load the generated audio
    audio = AudioSegment.from_file("../temp_output.mp3")

    # Trim or pad the audio to match the specified duration
    if len(audio) < duration:
        silence = AudioSegment.silent(duration=duration - len(audio))
        segment_audio = audio + silence
    else:
        segment_audio = audio[:duration]

    return segment_audio
'''def pitch_shift(audio, semitones):
    # Convert audio to a numpy array
    audio_data = np.array(audio.get_array_of_samples())

    # Calculate the pitch shift factor
    pitch_shift_factor = 2 ** (semitones / 12.0)

    # Apply pitch shift to the audio data
    shifted_data = np.interp(
        np.arange(0, len(audio_data), pitch_shift_factor),
        np.arange(0, len(audio_data)),
        audio_data
    ).astype(np.int16)

    # Create a new AudioSegment from the shifted data
    shifted_audio = AudioSegment(
        shifted_data.tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=shifted_data.dtype.itemsize,
        channels=audio.channels
    )

    return shifted_audio'''
@app.route("/", methods=["GET", "POST"])
def index():
    languages = tts_langs()
    if request.method == "POST":
        link = request.form["link"]
        print(link)
        dest_lang = request.form["target_lang"]
        video_id = link.split("v=")[1]
        srt = YouTubeTranscriptApi.get_transcript(video_id)
        lis = []
        y = []
        for i in srt:
            lis.append(i)
            y.append(i["duration"])
        translator = Translator()
        '''languages = tts_langs()
        print(y)
        print('Select the target Language: ')
        for i, (lang_code, lang_name) in enumerate(languages.items()):
            print(f"{i}: {lang_name}")'''

        '''target_lang_index = int(input("Enter the index of the target language: "))
        dest_lang = list(languages.keys())[target_lang_index]'''

        current_time = 0
        segment_audios = []
        audio = AudioSegment.silent(duration=0)
        for idx, caption in enumerate(lis):
            text = caption["text"]
            duration = caption["duration"] * 1000
            start = caption["start"] * 1000

            # Translate the English text to the destination language
            translated_text = translator.translate(text, src='en', dest=dest_lang).text
            segment_audio = generate_audio(translated_text, dest_lang, duration)
            semitones_to_shift = -3

            # Perform pitch shift
            '''segment_audio = pitch_shift(segment_audi, semitones_to_shift)'''
            silence_duration = start - current_time
            if silence_duration > 0:
                # Pad with silence if needed to match start time

                silence = AudioSegment.silent(duration=silence_duration)
                audio += silence
                current_time += silence_duration
            print(translated_text)

            if idx == 0:
                # For the first audio file, extract the segment before the time_to_join
                audio += segment_audio[:duration]
            else:
                # For intermediate audio files, include the full segment

                audio_before = audio[:start]

                audio = audio_before + segment_audio

            current_time += duration

        audio.export("merged_output.mp3", format="mp3")
        yt = YouTube(link)
        print(link)
        # Choose the stream (resolution and format) you want to download
        stream = yt.streams.get_highest_resolution()

        # Specify the path where you want to save the downloaded video
        file_name = 'new_video'

        # Download the video
        stream.download(filename=file_name)

        print(f'Downloaded: {yt.title}')
        video_clip = VideoFileClip(file_name)
        audio_clip = AudioFileClip("merged_output.mp3")

        # Ensure the audio duration matches the video duration (trim or pad as needed)
        if audio_clip.duration > video_clip.duration:
            audio_clip = audio_clip.subclip(0, video_clip.duration)
        elif audio_clip.duration < video_clip.duration:
            video_clip = video_clip.subclip(0,audio_clip.duration)

        # Set the audio of the video to the synchronized audio
        video_clip = video_clip.set_audio(audio_clip)

        # Write the synchronized video with audio to a new file
        video_clip.write_videofile("synchronized_video.mp4", codec="libx264")

        return redirect(url_for("play_audio"))
    return render_template("index.html",languages=languages)
@app.route("/play_audio")
def play_audio():

    os.system("start synchronized_video.mp4")
    # Your code for playing the merged audio
    return send_file("../synchronized_video.mp4", as_attachment=True)
if __name__ == "__main__":
    app.run(debug=True)

