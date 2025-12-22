import os
import requests
import praw
from datetime import datetime

class SocialScraper:
    def __init__(self):
        self.client_id = os.environ.get("REDDIT_CLIENT_ID")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        self.user_agent = "AstaInsights_MVP/1.0"
        self.use_api = self.client_id and self.client_secret

    def scrape_reddit(self, limit=20):
        """Scans r/Ghana and r/Accra for real estate keywords."""
        print(f"   📡 Connecting to Reddit ({'Authenticated' if self.use_api else 'Public Mode'})...")
        
        subreddits = ["ghana", "accra"]
        keywords = ["rent", "land", "house", "apartment", "flood", "traffic", "crime", "expensive", "buy", "lease"]
        posts = []

        if self.use_api:
            # AUTHENTICATED (Better)
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            for sub in subreddits:
                try:
                    # Search for keywords
                    for submission in reddit.subreddit(sub).search(' OR '.join(keywords), sort='new', limit=limit):
                        posts.append({
                            "source_id": submission.id,
                            "platform": "reddit",
                            "url": submission.url,
                            "content": f"{submission.title} \n {submission.selftext[:500]}",
                            "created_at": datetime.fromtimestamp(submission.created_utc).isoformat()
                        })
                except Exception as e:
                    print(f"      ⚠️ API Error on r/{sub}: {e}")
        else:
            # PUBLIC (Fallback)
            headers = {'User-Agent': self.user_agent}
            for sub in subreddits:
                try:
                    url = f"https://www.reddit.com/r/{sub}/search.json?q={' OR '.join(keywords)}&sort=new&limit={limit}&restrict_sr=1"
                    res = requests.get(url, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        for item in data['data']['children']:
                            post = item['data']
                            posts.append({
                                "source_id": post['id'],
                                "platform": "reddit",
                                "url": f"https://reddit.com{post['permalink']}",
                                "content": f"{post['title']} \n {post.get('selftext', '')[:500]}",
                                "created_at": datetime.fromtimestamp(post['created_utc']).isoformat()
                            })
                except Exception as e:
                    print(f"      ⚠️ Public Scrape Error on r/{sub}: {e}")

        print(f"   📥 Found {len(posts)} Reddit discussions.")
        return posts
