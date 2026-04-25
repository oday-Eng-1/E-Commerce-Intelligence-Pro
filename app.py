import httpx
import asyncio
from flask import Flask, request, jsonify
from selectolax.parser import HTMLParser
import random

app = Flask(__name__)

class EnterpriseScraper:
    def __init__(self):
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]

    async def fetch_page(self, url):
        headers = {
            "User-Agent": random.choice(self.ua_list),
            "Accept-Language": "en-US,en;q=0.9",
        }
        # Using a context manager for reliability
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
                return response.text if response.status_code == 200 else None
            except Exception:
                return None

    def parse_amazon(self, html):
        if not html:
            return {"error": "Failed to fetch page"}
            
        tree = HTMLParser(html)
        
        # Safe extraction logic to prevent 500 errors
        title_node = tree.css_first("span#productTitle")
        price_node = tree.css_first("span.a-offscreen")
        img_node = tree.css_first("img#landingImage")
        
        # Building response with fallback values
        return {
            "metadata": {"version": "2.1", "status": "Success"},
            "product": {
                "title": title_node.text().strip() if title_node else "Protection Triggered or Title Not Found",
                "price": price_node.text().strip() if price_node else "Check Website",
                "image": img_node.attributes.get("src") if img_node else "N/A"
            }
        }

scraper = EnterpriseScraper()

@app.route('/v2/extract')
def extract():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "No URL provided"}), 400

    # Handling the Async part safely inside Flask
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        html_content = loop.run_until_complete(scraper.fetch_page(target_url))
        loop.close()
        
        data = scraper.parse_amazon(html_content)
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run()
