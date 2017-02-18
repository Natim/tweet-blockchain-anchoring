import aiohttp
import async_timeout
import asyncio
import hashlib
import json
import os

# ENV config
#
# - WOLEET_BEARER_TOKEN: mandatory
# - TWITTER_BEARER_TOKEN: mandatory
# - KINTO_SERVER: default to `https://kinto.dev.mozaws.net/v1`
# - KINTO_AUTH: default to `user:pass`
#

BUCKET_ID = "tweet_blockchain_anchoring"
FREQUENCY_SECONDS = 10
FOLLOWED_USERS = ["JLMelenchon", "MarCharlott", "benoithamon", "yjadot", "EmmanuelMacron",
                  "FrancoisFillon", "MLP_officiel", "f_philippot"]

WOLEET_SERVER = 'https://api-preprod.woleet.io/v1'
WOLEET_HEADERS = {'Authorization': 'Bearer {}'.format(os.getenv('WOLEET_BEARER_TOKEN')),
                  'Content-Type': 'application/json'}

KINTO_SERVER_URL = os.getenv('KINTO_SERVER', 'https://kinto.dev.mozaws.net/v1').rstrip('/')
KINTO_AUTH = os.getenv('KINTO_AUTH', 'user:pass').split(':', 1)
KINTO_BASIC_AUTH = aiohttp.BasicAuth(*KINTO_AUTH, encoding='utf-8')

TWITTER_HEADERS = {'Authorization': 'Bearer {}'.format(os.getenv('TWITTER_BEARER_TOKEN'))}
TWITTER_TIMELINE_URL = ('https://api.twitter.com/1.1/statuses/user_timeline.json'
                        '?screen_name={}&trim_user=1&count=20')
KINTO_HEADERS = {'Content-Type': 'application/json'}

USER_LAST_ID = {}


async def init_kinto_bucket_and_collections(session):
    bucket_url = '{}/buckets/{}'.format(KINTO_SERVER_URL, BUCKET_ID)
    print("Setting up {}".format(bucket_url))
    response = await session.put(bucket_url, headers=KINTO_HEADERS, auth=KINTO_BASIC_AUTH)
    response.raise_for_status()
    response.close()

    for collection in FOLLOWED_USERS:
        collection_url = '{}/buckets/{}/collections/{}'.format(
            KINTO_SERVER_URL, BUCKET_ID, collection)
        print("Setting up {}".format(collection_url))
        response = await session.put(collection_url, headers=KINTO_HEADERS, auth=KINTO_BASIC_AUTH)
        response.raise_for_status()
        response.close()


def canonical_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def generate_id(tweet):
    return hashlib.sha256(canonical_json(tweet).encode('utf-8')).hexdigest()


def currated_tweet(tweet):
    return {
        'user_id': tweet['user']['id_str'],
        'text': tweet['text'],
        'id': tweet['id_str'],
        'created_at': tweet['created_at'],
    }

async def handle_user(session, user):
    # Fetch user timeline
    tweets = await fetch_timeline(session, user)
    if len(tweets) > 0:
        anchors = await publish_tweets(session, user, tweets[::-1])
        await anchor_tweets(session, user, anchors)


# Fetch User timeline
async def fetch_timeline(session, user):
    with async_timeout.timeout(30):
        url = TWITTER_TIMELINE_URL.format(user)
        last_id = USER_LAST_ID.get(user)
        if last_id:
            url += '&since_id={}'.format(last_id)
        # XXX: Handle pagination
        async with session.get(url, headers=TWITTER_HEADERS) as response:
            response.raise_for_status()
            return await response.json()

async def publish_tweets(session, user, tweets):
    print('Publish {} tweets for {}'.format(len(tweets), user))
    requests = []

    for tweet in tweets:
        if USER_LAST_ID.get(user, '0') < tweet['id_str']:
            USER_LAST_ID[user] = tweet['id_str']

        if 'retweeted_status' in tweet:
            # Skip retweets
            continue

        proper_tweet = currated_tweet(tweet)
        requests.append({
            "body": {
                "data": {
                    "id": generate_id(proper_tweet),
                    "tweet": proper_tweet
                }
            }
        })

    request_body = {
        "defaults": {
            "method": "POST",
            "path": "/buckets/{}/collections/{}/records".format(BUCKET_ID, user),
        },
        "requests": requests
    }
    batch_url = '{}/batch'.format(KINTO_SERVER_URL)
    response = await session.post(batch_url, data=json.dumps(request_body),
                                  headers=KINTO_HEADERS,
                                  auth=KINTO_BASIC_AUTH)
    response.raise_for_status()
    body = await response.json()
    response.close()
    anchors = []
    for resp in body['responses']:
        if resp['status'] >= 400:
            raise ValueError('Record could not be created: {}'.format(resp['body']))
        anchors.append({'name': '{}:{}'.format(user, resp['body']['data']['tweet']['id']),
                        'hash': resp['body']['data']['id']})
    print("Published", user)
    return anchors

async def anchor_tweets(session, user, anchors):
    tasks = []
    requests = []
    for anchor in anchors:
        search_url = '{}/anchorids?hash={}'.format(WOLEET_SERVER, anchor['hash'])
        result = await session.get(search_url)
        body = await result.json()
        if body['totalElements'] == 0:
            url = '{}/anchor'.format(WOLEET_SERVER)
            tasks.append(session.post(url,
                                      data=json.dumps(anchor),
                                      headers=WOLEET_HEADERS))
        else:
            requests.append({
                "path": "/buckets/{}/collections/{}/records/{}".format(
                    BUCKET_ID, user, anchor['hash']),
                "body": {
                    "data": {
                        "receipts": {
                            "id": body['content'][0]
                        }
                    }
                }
            })

    responses = await asyncio.gather(*tasks)
    for response in responses:
        response.raise_for_status()
        body = await response.json()
        requests.append({
            "path": "/buckets/{}/collections/{}/records/{}".format(
                BUCKET_ID, user, response['hash']),
            "body": {
                "data": {
                    "receipts": {
                        "id": response['id']
                    }
                }
            }
        })
        response.close()

    request_body = {
        "defaults": {
            "method": "PATCH",
        },
        "requests": requests
    }
    batch_url = '{}/batch'.format(KINTO_SERVER_URL)
    response = await session.post(batch_url, data=json.dumps(request_body),
                                  headers=KINTO_HEADERS,
                                  auth=KINTO_BASIC_AUTH)
    response.raise_for_status()
    body = await response.json()
    response.close()
    anchors = []
    for resp in body['responses']:
        if resp['status'] >= 400:
            raise ValueError('Record could not be updated: {}'.format(resp['body']))



async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        print("Bot starting...")
        await init_kinto_bucket_and_collections(session)

        while True:
            # Every FREQUENCY_SECONDS seconds
            print("Polling for changes.")

            tasks = []
            # For each followed account
            for user in FOLLOWED_USERS:
                # Grab the timeline
                tasks.append(handle_user(session, user))

            await asyncio.gather(*tasks)
            await asyncio.sleep(FREQUENCY_SECONDS)


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
