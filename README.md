# Discourse

Lazybug integrates comments and discussion with a separate discourse instance.

## Installation

[Guide how to set up Discourse on a DigitalOcean droplet](https://www.digitalocean.com/community/tutorials/how-to-install-discourse-on-ubuntu-20-04)

## SSO

We use the accounts on the main site (lazybug.ai) as a SSO for Discourse. Here is the authentication flow:

1. User enters `lazybug.ai` and logs in. When logged in a JWT is stored in a cookie on this domain
2. User clicks "Discuss" which diverts them to `discourse.lazybug.ai`
3. Discourse server does a request to `lazybug.ai/api/discourse/sso` with an sso and sig token as query parameters (see `discourse_sso` [endpoint](https://github.com/martindbp/lazybug/blob/master/backend/app/app.py))
)
4. Lazybug server validates the sso and sig using the key in the `DISCOURSE_SECRET` env variable (created by admin on Discourse)
5. Lazybug server uses the JWT stored in the cookie to extract user id and email, and returns this info to Discourse
6. User is now logged in using their email on Discourse

## Prefilled comments

When a user wants to ask a question regarding a specific caption we link to the topic with a special query parameter "reply_quote", for example `https://discourse.lazybug.ai/t/lud-ngji-the-deer-and-the-cauldron/71?reply_quote=%3E+hello+world`. This prefills a reply with some text, where we can put the context of the specific caption (a link back to the video, the chinese etc), so that it's easier to ask a question about it. This context is thus generated on the lazybug.ai frontend and supplied through the query parameter.

This ability to add prefill a reply doesn't come with Discourse by default, but is implemented using a simple [plugin](https://github.com/martindbp/discourse-lazybug-plugin), which the [admin installs on the Discourd server](https://meta.discourse.org/t/install-plugins-in-discourse/19157).

## Automatically generated show/movie topics

In order for users to be able to comment on a specific video and show, one topic has to be generated for each show. This is done in `make_discourse_topics.py` by going through all the shows in `data/remote/public/shows/*.json`, checking if a topic for this show id exists and if not, create it through the Discourse API. Note that the DISCOURSE_API_KEY environment variable has to be set. This script also needs to save the internal Discourse topic id in the show json, in order for the frontend to be able to link to it.

Note that `make_discourse_topics.py` is run as part of the `show-list-full` make command, which bakes all the individual show files into one, creates bloom filters for the vocabulary etc.
