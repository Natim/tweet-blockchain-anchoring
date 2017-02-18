Tweet Blockchain Anchoring
==========================

This is a pet project that let you follow some tweeter account, backup and anchor their tweet in the blockchain.

Install and run
---------------

First of all `get an Oauth Bearer Token from Twitter`_.

Get your ``consumer_key`` and ``consumer_secret`` in the `Twitter APP Dashboard`_

.. _`get an Oauth Bearer Token from twitter`: https://dev.twitter.com/oauth/application-only#issuing-application-only-requests
.. _`Twitter APP Dashboard`: https://apps.twitter.com/

::
   
   http -f POST https://api.twitter.com/oauth2/token grant_type=client_credentials \
       --auth consumer_key:consumer_secret
   {"token_type":"bearer","access_token":"AAAAAAA...AAAAAAAAA"}

::

    TWITTER_BEARER_TOKEN="AAAAAAA...AAAAAAAAA" \
	KINTO_SERVER=https://kinto.dev.mozaws.net/v1/ \
	    make run-bot


More Information
----------------

* **Python**: 3.5+
* [**Deploy your own Kinto in one click**](http://kinto.readthedocs.io/en/stable/tutorials/install.html#deploying-on-cloud-providers)
* Anchoring is done using [Woleet](https://woleet.io/) API.
