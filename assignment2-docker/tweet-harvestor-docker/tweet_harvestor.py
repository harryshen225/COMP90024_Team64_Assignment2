### team 64 
## Harry Shen 957637 Melbourne
## Jiaqi Wang 908406
## Yisu Ren 1141462
## Chaoyin Chen 1225100



import couchdb
import tweepy
import json, re, os, time
from logger import Logger
from textblob import TextBlob
from mapReduce import *
import requests
import couchdb.design
from couchdb import Server

TWEETS_PATH = 'tweets.json'
GEOBOX_AUSTRALIA = [112.34,-44.04,153.98,-10.41]
KEYWORD_RE = r'( az )|(astrazeneca)|(pfizer)|(novavax)|(vaccination)|(vaccine)|(vaccinate)|(vaccinated)|( dose )|(booster)|( jab )|(inoculation)|(immunisation)|(immunization)'
logger = Logger("tweet_harvestor")
NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]
AZ_KEYS = {"az","astrazeneca"}
PZ_KEYS = {"pfizer"}
DB_NAME = "parsed-tweets"

URL = 'http://' + os.environ['SERVER_USERNAME'] + ':' + os.environ['SERVER_PASSWORD']+ '@' + os.environ['SERVER_IP'] + ':5984/'
DUP_VIEW_ADDR = 'http://'+ os.environ['SERVER_USERNAME'] +':' + os.environ['SERVER_PASSWORD']+'@'+ os.environ['SERVER_IP'] + \
                ":5984/parsed-tweets/_design/mapReduce/_view/dup_count?keys=%5B\""

suffix = "\"%5D&reduce=true&group=true"


# Subclass StreamListener
class CouchStreamListener(tweepy.StreamListener):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def on_data(self, data):
        if data[0].isdigit():
            pass
        else:
            json_data = json.loads(data)
            if re.search(KEYWORD_RE, json_data["text"].lower()) is not None:
                logger.log("New tweet: {}".format(json_data["text"]))
                with open(TWEETS_PATH, 'a') as tweets_file:
                    tweets_file.write(data)

                ftweet = reformattweet(json_data)

                if not isDuplicated(ftweet['id_str']):
                    self.db.save(ftweet)
                    callSync(self.db)


def callSync(db):
    couch_views = [
        DupCount(),
        CountTotal(),
        CitySentiments(),
        OverallSentiments(),
        PositiveSentimentPerState(),
        NegativeSentimentPerState(),
        NeutralSentimentPerState(),
        SentiByCityAndDate(),
        StrongPositiveSentimentPerState(),
        StrongNegativeSentimentPerState(),
        OverallStateSentiments(),
        StateSentiment(),
        pzView(),
        azView(),
        # Put other view classes here
    ]
    couchdb.design.ViewDefinition.sync_many(db, couch_views, remove_missing=True)

def isDuplicated(s):
    # duplication avoidance
    dup_url = DUP_VIEW_ADDR + s + suffix
    r = requests.get(url=dup_url)
    try:
        resp = dict(r.json())['rows']
    except:
        print("not Found")
        return False
    if not resp:
        return False
    return True

def reformattweet(tweet):
    ftweet = {}
    for feature in NECESSARY_CONTENTS:
        if feature == 'created_at':
            date_arr = tweet[feature].split()
            ftweet['date'] = date_arr[1] + ' ' + date_arr[2]
        if feature == "place":
            tmp = tweet[feature]
            ftweet["location"] = tmp["full_name"]
            locs = ftweet['location'].split(',')
            # print(locs)
            if len(locs) == 2:
                ftweet['state'] = ftweet['location'].split(',')[1]
                ftweet['city'] = ftweet['location'].split(',')[0]
            else:
                ftweet['state'] = ftweet['location']
                ftweet['city'] = ftweet['location']

            ftweet["country"] = tmp["country"]
            ftweet["bounding_box"] = {}
            for index, coord in enumerate(tmp["bounding_box"]["coordinates"][0]):

                if index == 0:
                    ftweet["bounding_box"]["xmin"] = coord[0]
                    ftweet["bounding_box"]["ymin"] = coord[1]
                elif index == 2:
                    ftweet["bounding_box"]["xmax"] = coord[0]
                    ftweet["bounding_box"]["ymax"] = coord[1]
            continue
        ftweet[feature] = tweet[feature]

    # keywords evaluation
    ftweet['tags'] = []
    # for w in PZ_KEYS:
    #     if w in ftweet['text']:
    #         ftweet['tags'].append("PZ")
    # for w in AZ_KEYS:
    #     if w in ftweet['text']:
    #         ftweet['tags'].append('AZ')
    words = ftweet['text'].split()
    for w in words:
        if w in AZ_KEYS:
            ftweet['tags'].append('AZ')
        if w in PZ_KEYS:
            ftweet['tags'].append('PZ')

    # Sentiment analysis
    blob = TextBlob(ftweet["text"])
    ftweet["polarity"] = blob.sentiment.polarity
    ftweet["subjectivity"] = blob.sentiment.subjectivity

    # Alternative: Add parsed tweet to local disk
    # with open(WRITE_PATH, 'w') as f:
    #     f.write(ftweet + '\n')

    return ftweet

# Initialize tweepy stream
def tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    couchStreamListener = CouchStreamListener(db)
    stream = tweepy.Stream(auth=api.auth, listener=couchStreamListener)
    logger.log("Tweepy stream is initialized.")
    while(True):
        try:
            stream.filter(locations=GEOBOX_AUSTRALIA)
        except:
            pass

# Connect CouchDB server
def couchdb_initializer():
    try:
        server = Server(url=URL)
        try:
            db = server[DB_NAME]
        except:
            db = server.create(DB_NAME)

            with open(TWEETS_PATH, 'r') as initial_tweets:
                for line in initial_tweets:
                    tweet = json.loads(line)
                    tweet = reformattweet(tweet)
                    db.save(tweet)
                    callSync(db)
        return db
    except:
        logger.log_error("Cannot find CouchDB Server...")
        raise

# Entry point
def run(consumer_key, consumer_secret, access_token, access_token_secret):
    db = couchdb_initializer()
    couchdb.design.ViewDefinition.sync(DupCount(), db)
    logger.log("Connected to CouchDB server.")
    callSync(db)
    tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db)

if __name__ == '__main__':
    time.sleep(60)
    run(os.environ['API_KEY'], os.environ['API_SECRET_KEY'], os.environ['ACESS_TOKEN'], os.environ['ACESS_TOKEN_SECRET'])