from flask import Blueprint, request, Response, current_app
from urllib.parse import unquote
import subprocess
import os
import logging

transcode_bp = Blueprint('transcode', __name__)

# Path to FFmpeg
FFMPEG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'ffmpeg_bin', 'ffmpeg-8.0.1-essentials_build', 'bin', 'ffmpeg.exe'
)

@transcode_bp.route('/transcode')
def transcode():
    """
    Real-time transcode MPEG-2 streams to H.264 for browser compatibility.
    Usage: /transcode?url=<stream_url>
    """
    source_url = unquote(request.args.get('url', ''))
    
    if not source_url:
        return "Missing URL parameter", 400
    
    logging.info(f"[TRANSCODE] Starting transcode for: {source_url}")
    
    # FFmpeg command to transcode to H.264 HLS
    # -re: read input at native frame rate
    # -i: input URL
    # -c:v libx264: encode video to H.264
    # -preset ultrafast: fastest encoding (lower quality but real-time)
    # -tune zerolatency: optimize for low latency
    # -c:a aac: encode audio to AAC
    # -f mpegts: output format MPEG-TS (streamable)
    # pipe:1: output to stdout
    
    cmd = [
        FFMPEG_PATH,
        '-re',  # Real-time
        '-i', source_url,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '2M',  # 2 Mbps video bitrate
        '-maxrate', '2M',
        '-bufsize', '4M',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-f', 'mpegts',
        '-'  # Output to stdout
    ]
    
    try:
        # Start FFmpeg process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=65536
        )
        
        def generate():
            """Stream FFmpeg output"""
            try:
                while True:
                    chunk = process.stdout.read(65536)
                    if not chunk:
                        break
                    yield chunk
            except GeneratorExit:
                process.kill()
            finally:
                process.kill()
                process.wait()
        
        response = Response(generate(), mimetype='video/mp2t')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'no-cache'
        return response
        
    except Exception as e:
        logging.error(f"[TRANSCODE] Error: {e}")
        return f"Transcode error: {e}", 500
