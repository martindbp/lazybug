# Introduction

[Lazybug](lazybug.ai) is a free and open source project for learning Chinese from TV and movies. Massive comprehensible (and compelling) input is one of the best ways to learn a language. Beginner material is rarely massive nor compelling, and TV is compelling and massive but not always comprehensible to beginners and intermediate learners. This project aims to make TV more comprehensible through interactive subtitles tailored to the individual learner, and aims to make all video available for study, no matter which website it's on.

The project consists of algorithms for extracting subtitles from video and processing the text, as well as a web app and browser extension for viewing and customaizing them, and saving/exporting vocabulary. In the future exercises and SRS (Spaced Repetition System) will be integrated.

The app (and browser extension) works more like a mobile app than a web app in that it stores all data locally in the browser and only syncs to the cloud on the user's request. The app is fully functional without a backend server, except in the cloud syncing functionality and forum. In the future the app will also be usable offline.

## Project Principles

1. Remain free and open source by minimizing hosting costs

Do as much processing as possible on the front-end rather on servers. For example:
  * Keep all logic client side (except account and social functionality), including ML inference (if possible)
  * Store user data client side and sync it to cheaper object storage rather than using SQL database server
  * Run heavy processing offline on local machines rather than in the cloud, such as extracting subtitles from video

2. Single Language (Chinese)

Supporting multiple languages creates a "Jack of all trades, master of none" kind of situation. Chinese is vastly different from any other language out there and requires very specific solutions that in general cannot be generalized to others.

3. Single Purpose

This project is for learning Chinese from TV and movies. While other functionality might grow out of it, this is priority number one. Things like learning how to write is best left for other apps.

4. Open Data and Format

The user should own their data, it should be easily exported.

Work towards an open data format for Chinese learning activity (impressions and SRS) to enable interoperability between apps. Today, a major inefficiency for learners is splitting their data between apps. A unified format/place for data would enable much more efficient scheduling for Spaced Repetition Systems, ranking of content etc.

5. Works Offline

The parts of the app that don't depend on a network (e.g. viewing videos) should work offline.

6. Copyright

This project provides content based on fair use doctrine:

1. "the purpose and character of the use, including whether such use is of a commercial nature or is for nonprofit educational purposes;"
   Interpretation: The full functionality of Lazybug is freely available and open source and could thus be seen as non-commercial educational in nature
2. "the nature of the copyrighted work;"
   Interpretation: the content is merely a written down and augmented version of what the user hears and sees (through hard or soft-subs) on the page. Google already does this when translating whole websites for end users.
3. "the amount and substantiality of the portion used in relation to the copyrighted work as a whole; and"
   Interpretation: videos themselves are not hosted nor copied, only the subtitles
4. "the effect of the use upon the potential market for or value of the copyrighted work."
   Interpretation: the project does not include subtitles for work that is illegally provided, e.g. only on legal sites like Youtube.com and Bilibili.com. The project does not interfere with ads or paid subscriptions. It also does not include subtitles where they could affect the creator financially, such as when PDF scripts are provided for Patreon supporters or available after paid subscription.

## DMCA

If you own the copyright to content hosted on lazybug.ai and it is being used inappropriately, please notify us at martin@lazybug.ai.

## Contributing

If you're interested in contributing to the project, here are some possible areas:

  * Processing shows - Finding good shows
  * Frontend (Vue.js / Quasar) - Design improvements, code cleanup and bug fixes very welcome
  * Machine Learning (Python, PyTorch, Segmentation, OCR, NLP) - There are plenty of interesting ML projects and improvements for processing videos and subtitles

Some work items may be found in the Github issues of this project, but before starting on anything please reach out to me@martindbp.com with details of your skillset and what you'd like to help out on.

## Reporting Bugs

If you have a Github account you can open an issue here, or you can create a new topic on the [forum](https://discourse.lazybug.ai/) (requires Lazybug account) with the category "Site Feedback and Bugs".

## General Project Structure

NOTE: this document is currently incomplete, as I'd adding to it as I revisit the different parts of the codebase.

This project consists of a number of different high-level parts:

1. Algorithms to extract Chinese captions from video, and process them in various ways, like performing sentence segmentation and word disambiguation. These algorithms are mostly implemented in Python.
2. A web app to watch videos, interact with and learn vocabulary, discuss and ask questions about content. The frontend is written in JS and Vue.js, the backend in Python.
3. A browser extension for viewing videos that cannot be embedded into the web app. The codebase is shared with the JS web app.

# Code and development details

## Backend server

The Python backend is meant to be simple and do mainly lightweight work in order to keep costs down. It's used for few things:
1. Serve the static frontend files (js, html and images). These files are then cached on Cloudflare CDN until updated.
2. User accounts and authentication
3. Managing the syncing of personal data to Backblaze B2
4. Discourse Single Sign On

### Production dev notes

The server can be run with the command `make run-server` for local development, or `make run-server-prod` on the production server.
On prod, server can be conveniently killed with `make kill-server`

The server needs a cert in `data/local/ssl_keys/{privkey,fullchain}.pem`. Create one in [Cloudflare](#cloudflare) and copy them here.

## Frontend

To release new frontend changes do:
1. `ssh root@$LAZYBUG_SERVER_IP`
2. `cd lazybug && make update-server`  # this kills the server, pulls changes, builds the frontend and runs the server again
3. The previous command purges the Cloudflare cache, but this sometimes doesn't work, in that case go to cloudflare and do "Purge Cache -> Purge Everything"

## Environment variables

These environment variables need to be set for the server if not LOCAL is set:

1. DISCOURSE_SECRET: for Discourse SSO. Secret is created in the UI when setting up DiscordConnect
2. B2_ENDPOINT, B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY: keys for integrating with Backblaze B2, for creating upload and download links for personal data

<a name="localfrontend"></a>
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
make run-server-local
```

## Data (Backblaze B2 and Cloudflare CDN)

All data (besides Discourse and the backend user auth data), including things like captions and user databases are stored as plain files in Backblaze B2 (S3 compatible) and served through Cloudflare CDN. Transfering data from Backblaze to Cloudflare is free due to an agreement between them, and Cloudflare CDN is free which makes this a very cost efficient combination. Backblaze storage cost is 1/2 of Amazon S3, and 1/10 the download fees (outside of Cloudflare), and no upload fees.

### Buckets

Captions, show data, dictionaries and other public data is stored in a public bucket accessible at `https://cdn.lazybug.ai/file/lazybug-public/`. Personal user data, such as the interaction log and user settings are stored in a private bucket at `https://cdn.lazybug.ai/file/lazybug-accounts/`. Other data, which we don't want/need to serve to users is stored in another private bucket.

The accounts bucket, being private cannot be served through the CDN, and therefore we have to pay data fees for when users download their personal database (upload is free). Downloads are $0.01/GB. Downloads should only happen when the user switches clients or logs out/in. 10k downloads per day @ 5MB amounts to $15/month. By the time this becomes expensive we can switch to something more fine-grained than syncing the entire database every time.

### Versioning and Syncing

For captions and other data, we want to keep old versions of the same file in case it's updated but references to it remain elsewhere in user data. We also want to reduce the number of requests and amount of data we pull from Cloudflare (and Backblaze), even if it's free (minimizing waste is the decent thing to do), therefore we want to make files immutable so that Cloudflare doesn't have to keep fetching from Backblaze to see if the data changed.

1. We store a `{filename}.hash` with the SHA256 content hash of the file, and the contents at `{filename}-{hash}.{ext}`
2. When the file changes, we save the new version in a new file with the hash in the filname and update the .hash file to point to it
3. We then upload the new files with the `make push-public` command.
4. We then use the `purge_cache` Cloudflare API to purge the .hash files from the cache, so that clients will download the new one This can be done for all files in `data/remote/public` by calling the `make purge-cloudflare-public` command.

We also cache files in the IndexedDB for lazybug.ai in order to minimize uncessary fetching from Cloudflare as the browser cache can be unreliable.

### User account data

User data is stored in the browser IndexedDB of lazybug.ai and is synced to the private lazybug-accounts bucket on Backblaze via the Python backend. This is done by exporting the database file, calling the `/api/signed-upload-link/{size}` end-point, which will in turn authenticate the user and call the B2 API to get a signed upload link for that user's database file. When the frontend receives this URL, which is valid for a temporary duration, it simply uploads the file directly to it. This avoids having to send the data to our backend first, which saves on bandwidth. The same goes for downloads, but instead using the `api/signed-download-link` endpoint. 

### Backblaze Settings

Cache header for lazybug-public: `{"cache-control":"max-age=31536000"}`

Update cors rules for lazybug-accounts bucket to allow signed upload/download URLs:
```
b2 update-bucket --corsRules '[{"corsRuleName":"uploadDownloadFromAnyOrigin", "allowedOrigins": [""], "allowedHeaders": [""], "allowedOperations": ["s3_delete", "s3_get", "s3_head", "s3_post", "s3_put"], "maxAgeSeconds": 3600}]' lazybug-accounts allPublic
```

<a name="cloudflare"></a>
### Cloudflare Settings

1. SSL/TLS mode should be set to Full (strict)
2. SSL/TLS -> Origin Server: The Python backend needs a certificate for serving HTTPS, which can be created/downloaded here
3. SSL/TLS -> Edge Certificates -> Always Use HTTPS (ON)
4. Rules -> Page Rules:
    * `discourse.lazybug.ai/*` | Disable Performance  (https://meta.discourse.org/t/how-do-you-setup-cloudflare/32258/22?page=2)
    * `lazybug.ai/static/*` | Browser Cache TTL: 2 minutes, Cache Level: Cache Everything
    * `cdn.lazybug.ai/file/lazybug-public/*` | Cache Level: Cache Everything

## Discourse

Lazybug integrates comments and discussion with a separate discourse instance.

### Installation

[Guide how to set up Discourse on a DigitalOcean droplet](https://www.digitalocean.com/community/tutorials/how-to-install-discourse-on-ubuntu-20-04)

### SSO

We use the accounts on the main site (lazybug.ai) as a SSO for Discourse. Here is the authentication flow:

1. User enters `lazybug.ai` and logs in. When logged in a JWT is stored in a cookie on this domain
2. Embed a hidden iframe pointing to `discourse.lazybug.ai`.
3. When loading the iframe, the discourse server does a request back to `lazybug.ai/api/discourse/sso` with an sso and sig token as query parameters (see `discourse_sso` [endpoint](https://github.com/martindbp/lazybug/blob/master/backend/app/app.py))
)
4. Lazybug server validates the sso and sig using the key in the `DISCOURSE_SECRET` env variable (created by admin on Discourse)
5. Lazybug server uses the JWT stored in the cookie to extract user id and email, and returns this info to Discourse
6. Discourse sets session tokens in the cookies for discourse.lazybug.ai
7. User is now logged in using their email on Discourse
8. When the user logs out from Lazybug, we call the Python server endpoint at `/api/discourse/logout` which calls the Discourse API to log the user out. This can't be done from the frontend because it requires a CSRF token.

See [this article](https://meta.discourse.org/t/setup-discourseconnect-official-single-sign-on-for-discourse-sso/13045) for enabling SSO on Discourse.


### Prefilled comments

When a user wants to ask a question regarding a specific caption we link to the topic with a special query parameter "reply_quote", for example `https://discourse.lazybug.ai/t/lud-ngji-the-deer-and-the-cauldron/71?reply_quote=%3E+hello+world`. This prefills a reply with some text, where we can put the context of the specific caption (a link back to the video, the chinese etc), so that it's easier to ask a question about it. This context is thus generated on the lazybug.ai frontend and supplied through the query parameter.

This ability to add prefill a reply doesn't come with Discourse by default, but is implemented using a simple [plugin](https://github.com/martindbp/discourse-lazybug-plugin), which the [admin installs on the Discourd server](https://meta.discourse.org/t/install-plugins-in-discourse/19157).

### Automatically generated show/movie topics

In order for users to be able to comment on a specific video and show, one topic has to be generated for each show. This is done in `make_discourse_topics.py` by going through all the shows in `data/git/shows/*.json`, checking if a topic for this show id exists and if not, create it through the Discourse API and save the topic slug and id in the show json. Note that the DISCOURSE_API_KEY environment variable has to be set. This script also needs to save the internal Discourse topic id in the show json, in order for the frontend to be able to link to it.

Note that `make_discourse_topics.py` is run as part of the `show-list-full` make command, which bakes all the individual show files into one, creates bloom filters for the vocabulary etc.

### Discourse API

Comments on a show topic is accessed directly from the frontend by the api at `discourse.lazybug.ai/t/{topic_id}.json`. Linking to a topic or a comment a comment requires the topic slug as well as the id, the URL template being `discourse.lazybug.ai/t/${topic_slug}/${topic_id}/${post_number}`. To enable this the `https://lazybug.ai` has to be added to acceptable CORS origins in the Discourse Admin UI. The value for "same site cookies" under Security also needs to be set to "None".

## Docker

There area two docker images which contains everything needed to build the frontend and run the server (martindbp/lazybug-server) and one for other processing such as extracting captions from videos etc (martindbp/lazybug-processing). To download one of them image run: `docker pull martindbp/lazybug-{server,processing}` or `make docker-pull` to download both.

To run a make command (e.g. `frontend`) inside a lazybug container, run `make docker-server COMMAND=frontend`. This maps a volume from current directory to the container so the container can access anything in the repository.
