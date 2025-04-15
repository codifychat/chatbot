
# 🐍 Codify — Learn. Code. Grow.
**Codify**  is a Telegram chatbot built with Python and Telegram API's, designed to help users learn programming fundamentals interactively. 🚀
## Features ✨
-  Learn programming basics right within Telegram.
-  Interactive and user-friendly experience.
-   Stores user sessions using SQLite for progress tracking.
## Installation 📦
### Using Docker 🐳
1.  Pull the latest image:
	```bash
	docker pull codifychatbot/codifychatbot:latest
	```
2. Run the Docker container:
	```bash
	docker run -d --name codifychatbot -e TELEGRAM_BOT_TOKEN=your_telegram_bot_token codifychatbot/codifychatbot:latest
	```
Replace `your_telegram_bot_token` with your actual Telegram bot token.
### Manual Installation 🛠️
1. Clone the repository:
	```bash
	git clone https://github.com/codifychat/chatbot
	```
2. Navigate to the project directory and run the chatbot:
	```bash
	python main.py
	```
3. Set up the bot token:
-    Create a file named `.env` in the bot's directory.
-   Add your Telegram bot token to the `.env` file like this:
	```bash
	TELEGRAM_BOT_TOKEN=your_telegram_bot_token
	```

## Dependencies 📚

Codify relies on a combination of Python standard libraries and third-party packages for its functionality. Below is the detailed breakdown:
### **Standard Libraries**
 - `asyncio`: For handling asynchronous operations.
 - `datetime`: For date and time manipulations.
 - `logging`: For detailed application logging.
 - `os`: To interact with the operating system and environment variables.
 - `sqlite3`: To manage user session storage effectively.
 - `contextlib`: For creating and managing context managers.
 - `logging.handlers.TimedRotatingFileHandler`: For advanced logging with file rotation.
### Third-Party Libraries
Make sure to install these dependencies before running the bot:
 - `colorama`: For colorful terminal output.
 - `nest_asyncio`: To allow nested asyncio event loops.
 - `dotenv`: For loading environment variables securely from `.env` files.
 - `python-telegram-bot`: The core library for interacting with the Telegram API.
### Installation Tip
To install the required Python libraries, run the following:
```bash
pip install -r requirements.txt
```
Ensure the `requirements.txt` file includes:
 - colorama
 - nest_asyncio
 - python-telegram-bot
 - python-dotenv
## Contributing 🤝
We welcome contributions to Codify! Feel free to:
-   Submit issues or suggestions.
-   Fork the repository and create pull requests.
## Disclaimer ⚠️
Make sure your Telegram bot token is stored securely and never shared publicly. Codify is designed for educational purposes.

Happy coding! ✌️
