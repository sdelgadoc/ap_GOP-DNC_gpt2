import gpt_2_simple as gpt2
import twint
import datetime
import tweepy
from keys import keys
import os

# Set the working directory to this Python file's path
file_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# General parameters
day_offset = 2
models = ['538', 'DNC', 'GOP']
tweet_files = {"DNC": "",
               "GOP": "",
               "538": "gpt2_gentext_clean.csv"
               }

prompt_accounts = {"DNC": "ap",
                   "GOP": "ap",
                   "538": "NateSilver538"
                   }


for model in models:
    # Calculate the time difference between now and noon today
    today_noon = datetime.datetime.now().strftime("%m/%d/%y")
    today_noon = datetime.datetime.strptime(today_noon + " 12:00:00", '%m/%d/%y %H:%M:%S')
    today = datetime.datetime.now()
    day_difference = today - today_noon
    day_difference = day_difference.seconds / 60 + day_difference.days * 86400
    
    # If we should pull a tweet from a file
    if tweet_files[model] != "" and day_difference > 0:
        # Read the latest index for the tweet file
        with open(file_directory + "/id." + tweet_files[model], 'r') as read_file:
            index = int(read_file.read())
        
        # Iterate through the file until you find the latest tweet
        with open(file_directory + "/" + tweet_files[model], 'r') as read_file: 
            for i in range(0,index + 1):
                tweet = read_file.readline()
        
        # Write the new index into the file
        with open(file_directory + "/id." + tweet_files[model], 'w') as write_file:
            write_file.write(str(index + 1))
    # Use the model to generate a tweet        
    else:   
        # Tweet prompt parameters
        word_count = 3
        
        # Get dates for tweet filtering
        today = datetime.date.today()
        today = today - datetime.timedelta(days = day_offset)
        yesterday = today - datetime.timedelta(days = 2)
        
        
        # Get tweets based on date filters
        c = twint.Config()
        c.Username = prompt_accounts[model]
        c.Store_object = True
        c.Since = yesterday.strftime("%Y-%m-%d")
        c.Until = today.strftime("%Y-%m-%d")
        twint.run.Search(c)
        
        # If you found more than one tweet
        if len(twint.output.tweets_list) > 0:
            # Find the tweet with the most likes
            max_likes_count = 0
            idx_max_likes_count = 0 
            
            for idx, tweet in enumerate(twint.output.tweets_list):
                if int(tweet.likes_count) > max_likes_count:
                    max_likes_count = int(tweet.likes_count)
                    idx_max_likes_count = idx
                
            # Get the first words of the most liked tweet
            split_tweet = twint.output.tweets_list[idx].tweet.split()
            tweet_prompt = ""
            
            for idx, word in enumerate(split_tweet):
                if idx < word_count:
                    tweet_prompt = tweet_prompt + word + " "
            
            tweet_prompt = tweet_prompt.strip(" ")
            
            
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
            
            gpt2.reset_session(sess)
        
    # Clean the tweet string
    tweet = tweet.replace("\"]","")
    tweet = tweet.replace("[\"","")
    tweet = tweet.replace("\']","")
    tweet = tweet.replace("[\'","")
    tweet = tweet.replace("\\n","\n")
    tweet = tweet.replace("\\'","\'")
    tweet = tweet[0:279]
    
    # Tweet using the twitter account
    consumer_key = keys[model]['consumer_key']
    consumer_secret = keys[model]['consumer_secret']
    access_token = keys[model]['access_token']
    access_token_secret = keys[model]['access_token_secret']
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    api = tweepy.API(auth)
    
    api.update_status(tweet)