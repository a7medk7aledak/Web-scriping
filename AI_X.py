import tweepy
import pandas as pd
from tabulate import tabulate  # مكتبة لتنسيق الجداول في الكونسول

# مفاتيح الوصول لـ Twitter API (تأكد من أن لديك وصولًا إلى v2)
bearer_token = "AAAAAAAAAAAAAAAAAAAAAMaLzQEAAAAAVHFcLizpuQ%2BAjUv4d21gNWphT0Y%3DEucm8cUjVl5jjB4EStwchKKhPlYkXbuBzGtlzAlDvDohiMdrJ2"

# توثيق الاتصال بـ API v2
client = tweepy.Client(bearer_token=bearer_token)

# البحث عن التغريدات حول "Bitcoin"
query = "Bitcoin -is:retweet lang:en"
tweets = client.search_recent_tweets(query=query, max_results=100, tweet_fields=["created_at", "text", "author_id"])

# استخراج النصوص وحفظها
data = [{"tweet": tweet.text, "user_id": tweet.author_id, "created_at": tweet.created_at} for tweet in tweets.data]
df = pd.DataFrame(data)
df.to_csv("bitcoin_tweets.csv", index=False)

print("✅ تم حفظ التغريدات بنجاح!")

# **عرض البيانات بشكل منسق في الكونسول**
print("\n📌 **عرض أول 10 تغريدات بشكل منسق:**\n")
print(tabulate(df.head(10), headers="keys", tablefmt="fancy_grid"))
