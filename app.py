import os
import subprocess
import whisper
from flask import Flask, render_template, request, jsonify, send_file
from threading import Thread

app = Flask(__name__, static_folder="static", template_folder="templates")

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Variable global para el progreso
progress_status = {"status": "idle", "message": "Esperando archivo..."}


def convert_video_to_audio(video_path, audio_path):
    command = [
        "ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return audio_path


def transcribe_audio(audio_path, language="es"):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language=language)
    return result["text"]


def process_video(video_path, output_txt_path):
    global progress_status
    try:
        progress_status = {"status": "processing", "message": "🎧 Convirtiendo video a audio..."}
        audio_path = os.path.join(OUTPUT_FOLDER, "audio.mp3")
        convert_video_to_audio(video_path, audio_path)

        progress_status = {"status": "processing", "message": "🧠 Transcribiendo con Whisper..."}
        transcription = transcribe_audio(audio_path, language="es")

        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        progress_status = {"status": "done", "message": "✅ Transcripción completada"}
    except Exception as e:
        progress_status = {"status": "error", "message": f"⚠️ Error: {str(e)}"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global progress_status
    video = request.files["video"]
    if not video:
        return jsonify({"error": "No se recibió ningún archivo."}), 400

    video_path = os.path.join(UPLOAD_FOLDER, video.filename)
    txt_path = os.path.join(OUTPUT_FOLDER, "transcription.txt")

    video.save(video_path)
    progress_status = {"status": "processing", "message": "📤 Archivo recibido. Iniciando proceso..."}

    # Ejecutar proceso en segundo plano
    thread = Thread(target=process_video, args=(video_path, txt_path))
    thread.start()

    return jsonify({"message": "Archivo cargado y proceso iniciado."})


@app.route("/progress")
def progress():
    return jsonify(progress_status)


@app.route("/download")
def download():
    txt_path = os.path.join(OUTPUT_FOLDER, "transcription.txt")
    if os.path.exists(txt_path):
        return send_file(txt_path, as_attachment=True)
    else:
        return jsonify({"error": "Archivo no encontrado."}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
    