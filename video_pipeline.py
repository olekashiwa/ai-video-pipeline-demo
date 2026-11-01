import os
import subprocess
import logging
import requests
import shutil
from gtts import gTTS
from mutagen.mp3 import MP3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROMPT = "A futuristic cyberpunk city at night, neon lights, rain, highly detailed, 8k, vertical"
TEXT_TO_SPEECH = "Добро пожаловать в город будущего. Здесь технологии и люди сливаются в единое целое."
OUTPUT_DIR = "./output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg не найден! Установите: sudo apt install ffmpeg")
    logger.info("FFmpeg найден и готов к работе.")

def generate_image(prompt: str) -> str:
    logger.info("Генерация изображения...")
    image_path = os.path.join(OUTPUT_DIR, "image.png")
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=1080&height=1920&nologo=true&seed=42"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(image_path, "wb") as f:
        f.write(response.content)
    logger.info(f"Изображение сохранено: {image_path}")
    return image_path

def generate_audio(text: str) -> str:
    logger.info("Генерация аудио через gTTS...")
    audio_path = os.path.join(OUTPUT_DIR, "audio.mp3")
    tts = gTTS(text=text, lang="ru", slow=False)
    tts.save(audio_path)
    logger.info(f"Аудио сохранено: {audio_path}")
    return audio_path

def get_audio_duration(audio_path: str) -> float:
    audio = MP3(audio_path)
    return audio.info.length

def assemble_video(image_path: str, audio_path: str, duration: float) -> str:
    logger.info("Сборка видео через FFmpeg...")
    output_path = os.path.join(OUTPUT_DIR, "final_reel.mp4")
    filter_complex = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0015,1.2)':d=1:s=1080x1920:fps=30"
    command = ["ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path, "-vf", filter_complex, "-c:v", "libx264", "-t", str(duration), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Ошибка FFmpeg:\n{result.stderr}")
        raise RuntimeError("Сбой при сборке видео")
    logger.info(f"Видео успешно собрано: {output_path}")
    return output_path

def main():
    logger.info("=== ЗАПУСК ПЛАЙПЛАЙНА ===")
    try:
        check_ffmpeg()
        img_path = generate_image(PROMPT)
        aud_path = generate_audio(TEXT_TO_SPEECH)
        duration = get_audio_duration(aud_path)
        final_video = assemble_video(img_path, aud_path, duration)
        logger.info("=== ПЛАЙПЛАЙН ЗАВЕРШЕН УСПЕШНО ===")
        print(f"\n✅ ГОТОВО! Файл сохранен: {os.path.abspath(final_video)}")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()