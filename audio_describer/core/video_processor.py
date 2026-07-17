# audio_describer/core/video_processor.py
from audio_describer.i18n_setup import _
import os
import subprocess
import tempfile
import sys
import json
import math

from audio_describer import config
from audio_describer.utils.logger import app_logger
from audio_describer.core import youtube_downloader
from audio_describer.models import config_model
from audio_describer.utils.system_utils import run_command, get_ffmpeg_path

FFMPEG_COMMAND = get_ffmpeg_path('ffmpeg')
FFPROBE_COMMAND = get_ffmpeg_path('ffprobe')

TEMP_PROCESSING_BASE_DIR = os.path.join(os.getcwd(), config.TEMP_DIR_NAME)
TEMP_VIDEO_DIR = os.path.join(TEMP_PROCESSING_BASE_DIR, "processed_videos")
if not os.path.exists(TEMP_VIDEO_DIR):
    os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)

try:
    ffmpeg_process = run_command([FFMPEG_COMMAND, "-version"])
    FFMPEG_IS_AVAILABLE = "ffmpeg version" in ffmpeg_process.stdout.lower() and ffmpeg_process.returncode == 0
    if not FFMPEG_IS_AVAILABLE:
        app_logger.warning(f"FFmpeg check failed. Command: '{FFMPEG_COMMAND}'. RC: {ffmpeg_process.returncode}. Stderr: {ffmpeg_process.stderr.strip()}")

    ffprobe_process = run_command([FFPROBE_COMMAND, "-version"])
    FFPROBE_IS_AVAILABLE = "ffprobe version" in ffprobe_process.stdout.lower() and ffprobe_process.returncode == 0
    if not FFPROBE_IS_AVAILABLE:
        app_logger.warning(f"FFprobe check failed. Command: '{FFPROBE_COMMAND}'. RC: {ffprobe_process.returncode}. Stderr: {ffprobe_process.stderr.strip()}")
except Exception as e:
    app_logger.error(f"A critical error occurred during FFmpeg/FFprobe availability check: {e}", exc_info=True)
    FFMPEG_IS_AVAILABLE = False
    FFPROBE_IS_AVAILABLE = False


def get_video_duration(video_path):
    if not FFPROBE_IS_AVAILABLE:
        app_logger.warning("ffprobe not available, cannot get video duration for chunking.")
        return 0.0
    
    command = [
        FFPROBE_COMMAND, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    process = run_command(command)
    if process.returncode == 0 and process.stdout.strip():
        try:
            return float(process.stdout.strip())
        except ValueError:
            return 0.0
    return 0.0

def get_video_properties(video_path):
    if not FFPROBE_IS_AVAILABLE:
        app_logger.warning("ffprobe not available, cannot get video properties.")
        return None
    command = [
        FFPROBE_COMMAND, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,bit_rate",
        "-of", "json", video_path
    ]
    process = run_command(command)
    if process.returncode == 0 and process.stdout.strip():
        try:
            props = json.loads(process.stdout)['streams'][0]
            if 'avg_frame_rate' in props and '/' in props['avg_frame_rate']:
                num, den = props['avg_frame_rate'].split('/')
                if int(den) != 0:
                    props['avg_frame_rate'] = float(num) / float(den)
                else:
                    props['avg_frame_rate'] = 30 
            else:
                 props['avg_frame_rate'] = 30
            if 'bit_rate' in props and props['bit_rate'] is not None:
                props['bit_rate'] = int(props['bit_rate'])
            else:
                props['bit_rate'] = None
            return props
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            app_logger.error(f"Failed to parse ffprobe output: {e}")
            return None
    return None

def _standardize_video_format(input_path, is_local_file=False):
    if not FFMPEG_IS_AVAILABLE:
        app_logger.warning("FFmpeg not available. Using original file for playback and analysis.")
        return input_path, not is_local_file

    _, extension = os.path.splitext(input_path)
    
    if extension.lower() == '.mp4':
        app_logger.info(f"Video '{os.path.basename(input_path)}' is already in MP4 container. Skipping standardization.")
        return input_path, not is_local_file

    app_logger.info(f"Repackaging '{os.path.basename(input_path)}' into MP4 container for maximum compatibility (fast process).")
    
    output_path = os.path.join(tempfile.gettempdir(), f"repackaged_{os.urandom(4).hex()}.mp4")

    command = [
        FFMPEG_COMMAND, "-y", "-i", input_path,
        "-c", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    process = run_command(command)
    if process.returncode != 0:
        app_logger.error(f"Failed to repackage video. Using original file. Error: {process.stderr}")
        return input_path, not is_local_file

    app_logger.info(f"Successfully repackaged video to temporary file: '{output_path}'")
    
    if not is_local_file:
        cleanup_temp_file(input_path)
        
    return output_path, True

def split_video_into_chunks(video_path, chunk_duration_sec, status_callback=None):
    if not FFMPEG_IS_AVAILABLE:
        raise RuntimeError("FFmpeg is required for video chunking but was not found.")
        
    total_duration = get_video_duration(video_path)
    if total_duration == 0:
        raise ValueError("Could not determine video duration or video is empty.")

    num_chunks = math.ceil(total_duration / chunk_duration_sec)
    if num_chunks <= 1:
        app_logger.info("Video is shorter than chunk size, no splitting needed.")
        return [video_path]

    if status_callback:
        status_callback(_("Splitting video into %d chunks...") % num_chunks)

    chunk_paths = []
    temp_dir = tempfile.gettempdir()
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    for i in range(num_chunks):
        start_time = i * chunk_duration_sec
        chunk_path = os.path.join(temp_dir, f"{base_name}_chunk_{i+1:03d}.mp4")
        
        command = [
            FFMPEG_COMMAND, "-y", "-ss", str(start_time), "-i", video_path,
            "-t", str(chunk_duration_sec), "-c", "copy", chunk_path
        ]
        
        process = run_command(command)
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed to create chunk {i+1}: {process.stderr}")
        
        chunk_paths.append(chunk_path)
        if status_callback:
            status_callback(_("Created chunk %d of %d...") % (i + 1, num_chunks))

    return chunk_paths

def preprocess_video_for_ai(original_video_path, status_update_callback=None):
    """Pre-processes video for AI analysis.

    FPS reduction is now handled natively by Gemini's videoMetadata parameter,
    so this function only handles audio stripping when requested.
    """
    if not FFMPEG_IS_AVAILABLE:
        if status_update_callback: status_update_callback(_("FFmpeg not found; using original video for AI."))
        return original_video_path, False

    should_silence = config_model.get_setting("send_silenced_video_to_ai")

    if not should_silence:
        app_logger.info("No pre-processing needed for AI video. FPS is handled by Gemini videoMetadata.")
        return original_video_path, False

    try:
        if status_update_callback: status_update_callback(_("Pre-processing video for AI analysis (stripping audio)..."))

        temp_dir = tempfile.gettempdir()
        video_basename = os.path.basename(original_video_path)
        name, ext = os.path.splitext(video_basename)
        processed_video_path = os.path.join(temp_dir, f"{name}_processed_{os.urandom(4).hex()}{ext}")

        ffmpeg_cmd = [
            FFMPEG_COMMAND, "-y", "-i", original_video_path,
            "-c:v", "copy", "-an",
            processed_video_path
        ]

        app_logger.info(f"Running FFmpeg pre-process command: {' '.join(ffmpeg_cmd)}")
        process = run_command(ffmpeg_cmd)

        if process.returncode != 0:
            err_msg = _("Failed to pre-process video; using original. Error: %s") % process.stderr
            if status_update_callback: status_update_callback(err_msg)
            app_logger.error(err_msg)
            return original_video_path, False

        if not os.path.exists(processed_video_path) or os.path.getsize(processed_video_path) < 1024:
            if status_update_callback: status_update_callback(_("Video pre-processing error; using original."))
            return original_video_path, False

        if status_update_callback: status_update_callback(_("Video pre-processing complete."))
        return processed_video_path, True

    except Exception as e:
        err_msg = _("Error during video pre-processing; using original. Error: %s") % e
        if status_update_callback: status_update_callback(err_msg)
        app_logger.error(err_msg, exc_info=True)
        return original_video_path, False


def process_local_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(_("Video file not found: %s") % file_path)
    return _standardize_video_format(file_path, is_local_file=True)

def process_direct_url(video_url):
    try:
        downloaded_file_path = youtube_downloader.download_video(video_url, output_dir=youtube_downloader.TEMP_DOWNLOAD_DIR, is_youtube_video=False)
        return _standardize_video_format(downloaded_file_path, is_local_file=False)
    except youtube_downloader.DownloaderError as e:
        raise youtube_downloader.DownloaderError(_("Failed to download from direct URL %s: %s") % (video_url, e))

def process_youtube_url(youtube_url, desired_resolution=None):
    try:
        app_logger.info(f"Attempting to download '{youtube_url}' as a YouTube video...")
        downloaded_file_path = youtube_downloader.download_video(
            video_url=youtube_url, 
            output_dir=youtube_downloader.TEMP_DOWNLOAD_DIR,
            desired_resolution=desired_resolution, 
            is_youtube_video=True
        )
        return _standardize_video_format(downloaded_file_path, is_local_file=False)
    except youtube_downloader.DownloaderError as e:
        app_logger.warning(f"Initial YouTube download failed for '{youtube_url}': {e}. Retrying as a direct URL...")
        
        try:
            downloaded_file_path = youtube_downloader.download_video(
                video_url=youtube_url, 
                output_dir=youtube_downloader.TEMP_DOWNLOAD_DIR, 
                is_youtube_video=False
            )
            return _standardize_video_format(downloaded_file_path, is_local_file=False)
        except youtube_downloader.DownloaderError as e2:
            final_error_message = _("Failed to download from YouTube URL %(url)s. "
                                    "Initial error: %(initial_error)s. "
                                    "Fallback attempt also failed: %(fallback_error)s") % {
                                        'url': youtube_url, 
                                        'initial_error': e, 
                                        'fallback_error': e2
                                    }
            raise youtube_downloader.DownloaderError(final_error_message)

def cleanup_temp_file(file_path):
    if not isinstance(file_path, str): return
    abs_file_path = os.path.abspath(file_path)
    is_in_downloader_temp = youtube_downloader.TEMP_DOWNLOAD_DIR in abs_file_path
    is_in_processor_temp = TEMP_VIDEO_DIR in abs_file_path
    is_in_generic_temp_name = config.TEMP_DIR_NAME in abs_file_path
    is_in_system_temp = tempfile.gettempdir() in abs_file_path

    if os.path.exists(abs_file_path) and (is_in_downloader_temp or is_in_processor_temp or is_in_generic_temp_name or is_in_system_temp):
        try:
            os.remove(abs_file_path)
            app_logger.info(f"Cleaned up temporary file: {abs_file_path}")
        except Exception as e:
            app_logger.error("Error cleaning up temporary file %s: %s" % (abs_file_path, e))