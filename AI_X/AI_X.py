# import tweepy
# import pandas as pd
# from tabulate import tabulate

# bearer_token = "AAAAAAAAAAAAAAAAAAAAAMaLzQEAAAAAhFE3MPJSdRzciEy5N3aJnScu6WM%3D8Yf5i0tbUI75F5hYJhb4REXhIbTf2ptuRHaQVwanKHHwoThYTX"

# client = tweepy.Client(bearer_token=bearer_token)

# query = "Bitcoin -is:retweet lang:en"
# tweets = client.search_recent_tweets(query=query, max_results=10, tweet_fields=["created_at", "text", "author_id"])

# data = [{"tweet": tweet.text, "user_id": tweet.author_id, "created_at": tweet.created_at} for tweet in tweets.data]
# df = pd.DataFrame(data)
# df.to_csv("bitcoin_tweets.csv", index=False)

# print("✅ Active tweets saved!")

# # **Display data in a formatted way in the console**
# print("\n📌 **Displaying the first 10 tweets in a formatted table:**\n")
# print(tabulate(df.head(10), headers="keys", tablefmt="fancy_grid"))

# # **Save data to a CSV file**



import pandas as pd
from tabulate import tabulate  # لجعل العرض أكثر تنظيمًا

# اسم الملف
file_path = "bitcoin_tweets.csv"

try:
    # قراءة الملف
    df = pd.read_csv(file_path)

    # عرض أول 10 صفوف بشكل منسق
    print("\n📌 **Displaying the first 10 rows of the CSV file:**\n")
    print(tabulate(df.head(10), headers="keys", tablefmt="fancy_grid"))
    
except FileNotFoundError:
    print("❌ Error: The file 'bitcoin_tweets.csv' was not found.")
except Exception as e:
    print(f"❌ An error occurred: {e}")
