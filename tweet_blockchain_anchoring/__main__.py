import os
import aiohttp
import asyncio
import async_timeout

FREQUENCY_SECONDS = 10
FOLLOWED_USERS = ["JLMelenchon", "MarCharlott", "benoithamon", "yjadot", "EmmanuelMacron",
                  "FrancoisFillon", "MLP_officiel", "f_philippot"]

TWITTER_HEADERS = {'Authorization': 'Bearer {}'.format(os.getenv('TWITTER_BEARER_TOKEN'))}
TWITTER_TIMELINE_URL = ('https://api.twitter.com/1.1/statuses/user_timeline.json'
                        '?screen_name={}&trim_user=1&count=10')

USER_LAST_ID = {}


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
    return await publish_tweets(session, user, tweets)


# Fetch User timeline
async def fetch_timeline(session, user):
    with async_timeout.timeout(30):
        url = TWITTER_TIMELINE_URL.format(user)
        last_id = USER_LAST_ID.get(user)
        if last_id:
            url += '&since_id = {}'.format(last_id)
        async with session.get(url, headers=TWITTER_HEADERS) as response:
            assert response.status == 200, await response.json()
            return await response.json()

async def publish_tweets(session, user, tweets):
    print(user, [currated_tweet(t) for t in tweets])


async def main(loop):
    print("Bot starting...")
    async with aiohttp.ClientSession(loop=loop) as session:
        # Every FREQUENCY_SECONDS seconds
        print("Polling for changes.")

        tasks = []
        # For each followed account
        for user in FOLLOWED_USERS:
            # Grab the timeline
            tasks.append(handle_user(session, user))

        tweets = await asyncio.gather(*tasks)
        print(tweets)
        await asyncio.sleep(FREQUENCY_SECONDS)


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
