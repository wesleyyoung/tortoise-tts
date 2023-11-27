import os

from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
DEFAULT_UPLOAD_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'tortoise', 'upload')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mp3'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_wav(video_path, wav_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_wav(wav_path)
    video.close()


def chunk_audio(wav_path, chunk_size=10):
    audio = AudioSegment.from_wav(wav_path)
    chunks = [audio[i:i + chunk_size * 1000] for i in range(0, len(audio), chunk_size * 1000)]
    return chunks


def process_video(file, video_path):
    if file and allowed_file(file.filename) and file.content_length <= MAX_FILE_SIZE:
        # Generate a secure filename and save the video file
        video_filename = secure_filename(file.filename)
        video_path = os.path.join(DEFAULT_UPLOAD_DIR, video_filename)
        file.save(video_path)
        os.makedirs(video_path, exist_ok=True)

        # Convert video to WAV
        wav_filename = video_filename.rsplit('.', 1)[0] + '.wav'
        wav_path = os.path.join(video_path, wav_filename)
        convert_to_wav(video_path, wav_path)

        # Chunk up the WAV file into 10-second clips
        audio_chunks = chunk_audio(wav_path, chunk_size=10)

        # Save each chunk as a separate WAV file
        for i, chunk in enumerate(audio_chunks):
            chunk_filename = f"{wav_filename.rsplit('.', 1)[0]}_chunk{i + 1}.wav"
            chunk_path = os.path.join(video_path, chunk_filename)
            chunk.export(chunk_path, format="wav")

        return True
    else:
        return False