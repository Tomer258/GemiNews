from flask import Flask
import TelegramScraper

app = Flask(__name__)

@app.route('/')
def hello():
    TelegramScraper.load_scraper()
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(debug=True)