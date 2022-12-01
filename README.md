# Backend server

The Python backend is meant to be simple and do mainly lightweight work in order to keep costs down. It's used for few things:
1. Serve the static frontend files (js, html and images). These files are then cached on Cloudflare CDN until updated.
2. User accounts and authentication
3. Managing the syncing of personal data to Backblaze B2
4. Discourse Single Sign On
5. Relay comments from the Discourse API

The server can be run with the command `make run-server` for local development, or `make run-server-prod` on the production server.
On prod, server can be conveniently killed with `make kill-server`

## Environment variables

These environment variables need to be set for the server if not LOCAL_ONLY is set:

1. DISCOURSE_API_KEY: for integration with the Discourse API. Secret can be created in the Admin UI
1. DISCOURSE_SECRET: for Discourse SSO. Secret is created in the UI when setting up DiscordConnect
2. B2_ENDPOINT, B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY: keys for integrating with Backblaze B2, for creating upload and download links for personal data

## Local SSL cert for Browser Extension development

In order to use the local backend server with the browser extension, you need a self-signed certificate for SSL. The reason for this is that in the browser extension we inject an iframe pointing at `https://localhost/static/iframe.html`. We then communicate with this iframe using message passing in order to load and save data. This way we don't have a syncronization problem between the extension and the website when the user uses both.

To generate a local certificate authority and the certificate and keys, run:
```
make local-ssl-cert
```
Any passphrase such as "1234" is fine, since it's for local use only.
After this command you need to import the CA.pem in the browser you use. In Chrome it's under "Settings"->"Security And Privacy"->"Security"->"Manage Certificates"->"Authorities"->"Import", then select `lazybug/data/local/ssl_certA/CA.pem`.

To run a local only version of the frontend and server, run:
```
# this, like `make frontend` builds the browser extension and web frontend,
# but with URLs pointing to localhost and other online features turned off
make local
# This runs the server for local development, in SSL mode
make run-server-local-only
```

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

See [this article](https://meta.discourse.org/t/setup-discourseconnect-official-single-sign-on-for-discourse-sso/13045) for enabling SSO on Discourse.

## Prefilled comments

When a user wants to ask a question regarding a specific caption we link to the topic with a special query parameter "reply_quote", for example `https://discourse.lazybug.ai/t/lud-ngji-the-deer-and-the-cauldron/71?reply_quote=%3E+hello+world`. This prefills a reply with some text, where we can put the context of the specific caption (a link back to the video, the chinese etc), so that it's easier to ask a question about it. This context is thus generated on the lazybug.ai frontend and supplied through the query parameter.

This ability to add prefill a reply doesn't come with Discourse by default, but is implemented using a simple [plugin](https://github.com/martindbp/discourse-lazybug-plugin), which the [admin installs on the Discourd server](https://meta.discourse.org/t/install-plugins-in-discourse/19157).

## Automatically generated show/movie topics

In order for users to be able to comment on a specific video and show, one topic has to be generated for each show. This is done in `make_discourse_topics.py` by going through all the shows in `data/remote/public/shows/*.json`, checking if a topic for this show id exists and if not, create it through the Discourse API. Note that the DISCOURSE_API_KEY environment variable has to be set. This script also needs to save the internal Discourse topic id in the show json, in order for the frontend to be able to link to it.

Note that `make_discourse_topics.py` is run as part of the `show-list-full` make command, which bakes all the individual show files into one, creates bloom filters for the vocabulary etc.
