import gpt_2_simple as gpt2
import twint
import datetime
import tweepy
import os
from keys import keys

# Set the working directory to this Python file's path
file_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_directory)

# Tweet prompt parameters
day_offset = 1
word_count = 3

# Get dates for tweet filtering
today = datetime.date.today()
today = today - datetime.timedelta(days = day_offset)
yesterday = today - datetime.timedelta(days = 1)

# Get tweets based on date filters
c = twint.Config()
c.Username = "ap_politics"
c.Store_object = True
c.Since = yesterday.strftime("%Y-%m-%d")
c.Until = today.strftime("%Y-%m-%d")
twint.run.Search(c)

# Find the tweet with the most likes
max_likes_count = 0
idx_max_likes_count = 0 

for idx, tweet in enumerate(twint.output.tweets_list):
    if int(tweet.likes_count) > max_likes_count:
        max_likes_count = int(tweet.likes_count)
        idx_max_likes_count = idx
    
# Get the first words of the most liked tweet
tweet_id = twint.output.tweets_list[idx].id
# Do a little clean up based on hard fought experience
split_tweet = twint.output.tweets_list[idx].tweet.replace("“","")
split_tweet = split_tweet.split()
tweet_prompt = ""

for idx, word in enumerate(split_tweet):
    if idx < word_count:
        tweet_prompt = tweet_prompt + word + " "

tweet_prompt = tweet_prompt.strip(" ")

# Create a list of the models you want to iterate through
models = ['DNC', 'GOP']


for model in models:
    # Generate the tweet using the gpt-2 model
    sess = gpt2.start_tf_sess()
    gpt2.load_gpt2(sess, run_name=model)
    
    tweet = gpt2.generate(sess,
                          run_name=model,
                          checkpoint_dir=file_directory + "/checkpoint",
                          length=100,
                          temperature=.7,
                          nsamples=1,
                          batch_size=1,
                          prefix=tweet_prompt,
                          truncate='<|endoftext|>',
                          include_prefix=True,
                          return_as_list=True
                         )[0]
    
    # Clean the tweet string
    tweet = tweet.strip("']")
    tweet = tweet.replace("\\n","\n")
    tweet = tweet.replace("\\'","\'")
    tweet = tweet.replace("“","")
    tweet = tweet[0:279]
    
    gpt2.reset_session(sess)
    
    # Tweet using the twitter account
    consumer_key = keys[model]['consumer_key']
    consumer_secret = keys[model]['consumer_secret']
    access_token = keys[model]['access_token']
    access_token_secret = keys[model]['access_token_secret']
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    api = tweepy.API(auth)
    
    api.update_status(tweet)