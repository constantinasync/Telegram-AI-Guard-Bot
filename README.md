An advanced AI-powered Telegram moderation bot designed to automatically detect and remove NSFW, violent, drug-related, weapon-related, and illegal visual content in Telegram groups.

This bot uses AWS Rekognition to analyze photos, videos, stickers, GIFs, and video notes, ensuring safer communities with minimal admin intervention.

⸻

🚀 Features

✅ AI Content Moderation
	•	Detects NSFW & explicit content
	•	Violence & graphic injury detection
	•	Drugs & tobacco content detection
	•	Weapons & hate symbols detection

✅ Full Media Coverage
	•	Photos
	•	Videos
	•	Animated & static stickers
	•	GIFs
	•	Video notes

✅ Smart Video Analysis
	•	Extracts multiple frames from videos & animated stickers
	•	Scans frames individually for maximum accuracy

✅ Automatic Actions
	•	Deletes dangerous content instantly
	•	Sends detailed alerts to admins & log groups

✅ Advanced Text Detection
	•	Detects ID cards, passports, driver licenses
	•	Detects drug-related text inside images

⸻

🧠 How It Works
	1.	Bot listens to messages in Telegram groups
	2.	Media files are downloaded securely
	3.	AI analyzes visual content using AWS Rekognition
	4.	If dangerous content is detected:
	•	Message is deleted
	•	Admins are notified with confidence scores

⸻

🛠 Technologies Used
	•	Python 3.10+
	•	python-telegram-bot v20+
	•	AWS Rekognition
	•	FFmpeg
	•	Pillow (PIL)
  ⸻
  
⚙️ Installation

1️⃣ Clone the repository
git clone https://github.com/constantinasync/telegram-ai-guard-bot.git
cd telegram-ai-guard-bot

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Configure environment variables
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_REGION=us-east-1

TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
ALERT_GROUP_ID=LOG_GROUP_ID
ADMIN_ID=ADMIN_USER_ID

⚠️ Never hardcode credentials in production.

▶️ Run the bot

python nsfwguard.py

🔐 Permissions Required
	•	Delete messages
	•	Read media messages
	•	Send messages to admin/log groups

Bot must be admin in the Telegram group.

⸻

📌 Roadmap
	•	User risk scoring system
	•	Auto-mute / auto-ban system
	•	Hybrid AI moderation (Vision LLM integration)
	•	Dashboard & statistics
	•	Multi-language admin alerts

⸻

⚠️ Disclaimer

This project is intended for educational and community moderation purposes only.

The author is not responsible for:
	•	False positives
	•	AWS usage costs
	•	Misuse of the software

Always review Telegram’s Terms of Service and local laws before deployment.

⸻

📜 License

MIT License
