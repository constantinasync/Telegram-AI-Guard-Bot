import logging
import boto3
import subprocess
import tempfile
import os
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ---------------- AWS Ayarları ----------------
AWS_ACCESS_KEY_ID = 'X'
AWS_SECRET_ACCESS_KEY = ''
AWS_REGION = 'X'

rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# ---------------- Telegram Ayarları ----------------
TELEGRAM_BOT_TOKEN = 'X'
ALERT_GROUP_ID = X
ADMIN_ID = X

# ---------------- Logging ----------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Yasaklı içerik etiketleri ----------------
DANGEROUS_LABELS = [
    # NSFW
    "Explicit Nudity", "Sexual Activity", "Sexual Content",

    # Violence / Terror
    "Violence", "Hate Symbols", "Terrorism", "Weapon Violence",

    # Drugs & Tobacco
    "Drugs", "Drug Use", "Drug Possession", "Drug Paraphernalia",
    "Marijuana", "Cannabis", "Weed", "Joint", "Hashish", "Opioid",
    "Heroin", "Cocaine", "Meth", "Ecstasy", "LSD", "Mushrooms",
    "Pills", "Products", "Drugs & Tobacco"
]

# ---------------- Fonksiyonlar ----------------
def check_moderation(file_bytes):
    
    try:
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': file_bytes},
            MinConfidence=70
        )
        labels = [label for label in response['ModerationLabels'] if label['Name'] in DANGEROUS_LABELS]
        return labels
    except Exception as e:
        logger.error(f"AWS Rekognition Moderation Error: {e}")
        return []

def check_for_drugs_and_id_content(file_bytes):
    
    try:
        response = rekognition.detect_text(Image={'Bytes': file_bytes})
        texts = [d['DetectedText'].lower() for d in response['TextDetections'] if d['Type'] == 'LINE']

        id_keywords = [
            'passport', 'identity card', 'driver license', 'birth date', 'nationality',
            'tc kimlik', 'kimlik kartı', 'ehliyet'
        ]
        drug_keywords = [
            'cocaine', 'heroin', 'marijuana', 'methamphetamine', 'drug trafficking',
            'illegal drugs', 'ecstasy', 'uyuşturucu', 'mdma', 'lsd', 'hashish',
            'skunk', 'opioid', 'fentanyl', 'meth', 'cannabis', 'cannabinoid', 'weed', 'dmt'
        ]

        id_match = any(any(keyword in text for keyword in id_keywords) for text in texts)
        drug_match = any(any(keyword in text for keyword in drug_keywords) for text in texts)

        return id_match or drug_match
    except Exception as e:
        logger.error(f"AWS DetectText Error: {e}")
        return False

async def convert_video_frame_to_jpeg(video_path, time_seconds):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        jpeg_path = tmp.name
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(time_seconds),
            "-i", video_path, "-vframes", "1", "-q:v", "2", jpeg_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(jpeg_path) and os.path.getsize(jpeg_path) > 0:
            with open(jpeg_path, "rb") as f:
                data = f.read()
            os.remove(jpeg_path)
            return data
        else:
            if os.path.exists(jpeg_path):
                os.remove(jpeg_path)
            return None
    except Exception as e:
        logger.error(f"FFmpeg frame extraction error: {e}")
        if os.path.exists(jpeg_path):
            os.remove(jpeg_path)
        return None

async def extract_gif_frames(gif_bytes, max_frames=10):
    frames = []
    try:
        gif_image = Image.open(BytesIO(gif_bytes))
        for i in range(max_frames):
            try:
                gif_image.seek(i)
                with BytesIO() as output:
                    frame = gif_image.convert("RGB")
                    frame.save(output, format="JPEG")
                    frames.append(output.getvalue())
            except EOFError:
                break
    except Exception as e:
        logger.error(f"GIF frame extraction error: {e}")
    return frames

async def handle_alert_and_delete(update, context, labels, text_flag):
    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Mesaj silinemedi: {e}")

    text = f"🚨 Tehlikeli içerik silindi!\nKullanıcı: {update.message.from_user.full_name}\n"
    if labels:
        text += "Rekognition: " + ", ".join([f"{l['Name']} ({l['Confidence']:.1f}%)" for l in labels]) + "\n"
    if text_flag:
        text += "AWS DetectText: Kimlik veya uyuşturucu içeriği tespit edildi.\n"

    await context.bot.send_message(chat_id=ALERT_GROUP_ID, text=text)
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

# ---------------- Ana moderation ----------------
async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file_bytes = None

        # ---------------- Fotoğraf ----------------
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file = await context.bot.get_file(file_id)
            file_bytes = await file.download_as_bytearray()
            labels = check_moderation(file_bytes)
            text_flag = check_for_drugs_and_id_content(file_bytes)
            if labels or text_flag:
                await handle_alert_and_delete(update, context, labels, text_flag)

        # ---------------- Sticker ----------------
        elif update.message.sticker:
            file_id = update.message.sticker.file_id
            file = await context.bot.get_file(file_id)
            if update.message.sticker.is_animated or update.message.sticker.is_video:
                with tempfile.TemporaryDirectory() as tmpdir:
                    webm_path = os.path.join(tmpdir, "sticker.webm")
                    await file.download_to_drive(webm_path)
                    for t in [0.5, 1, 1.5, 2, 2.5, 3]:
                        file_bytes = await convert_video_frame_to_jpeg(webm_path, t)
                        if not file_bytes:
                            continue
                        labels = check_moderation(file_bytes)
                        text_flag = check_for_drugs_and_id_content(file_bytes)
                        if labels or text_flag:
                            await handle_alert_and_delete(update, context, labels, text_flag)
                            return
            else:
                file_bytes = await file.download_as_bytearray()
                try:
                    img = Image.open(BytesIO(file_bytes))
                    with BytesIO() as output:
                        img.save(output, format="PNG")
                        file_bytes = output.getvalue()
                except UnidentifiedImageError:
                    return
                labels = check_moderation(file_bytes)
                text_flag = check_for_drugs_and_id_content(file_bytes)
                if labels or text_flag:
                    await handle_alert_and_delete(update, context, labels, text_flag)

        # ---------------- Video Note ----------------
        elif update.message.video_note:
            file_id = update.message.video_note.file_id
            file = await context.bot.get_file(file_id)
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = os.path.join(tmpdir, "video_note.mp4")
                await file.download_to_drive(video_path)
                for t in [0.5, 1, 1.5, 2, 2.5, 3]:
                    file_bytes = await convert_video_frame_to_jpeg(video_path, t)
                    if not file_bytes:
                        continue
                    labels = check_moderation(file_bytes)
                    text_flag = check_for_drugs_and_id_content(file_bytes)
                    if labels or text_flag:
                        await handle_alert_and_delete(update, context, labels, text_flag)
                        return

        # ---------------- Video ----------------
        elif update.message.video:
            file_id = update.message.video.file_id
            file = await context.bot.get_file(file_id)
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = os.path.join(tmpdir, "video.mp4")
                await file.download_to_drive(video_path)
                for t in [0.5, 1, 1.5, 2, 2.5, 3, 3.5]:
                    file_bytes = await convert_video_frame_to_jpeg(video_path, t)
                    if not file_bytes:
                        continue
                    labels = check_moderation(file_bytes)
                    text_flag = check_for_drugs_and_id_content(file_bytes)
                    if labels or text_flag:
                        await handle_alert_and_delete(update, context, labels, text_flag)
                        return

        # ---------------- GIF ----------------
        elif update.message.document and update.message.document.mime_type == "image/gif":
            file_id = update.message.document.file_id
            file = await context.bot.get_file(file_id)
            gif_bytes = await file.download_as_bytearray()
            frames = await extract_gif_frames(gif_bytes, max_frames=10)
            for frame_bytes in frames:
                labels = check_moderation(frame_bytes)
                text_flag = check_for_drugs_and_id_content(frame_bytes)
                if labels or text_flag:
                    await handle_alert_and_delete(update, context, labels, text_flag)
                    return

    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

# ---------------- Main ----------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.ALL, moderate))
    app.run_polling()

if __name__ == '__main__':
    main()