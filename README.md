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

# Data (Backblaze B2 and Cloudflare CDN)

All data (besides Discourse and the backend user auth data), including things like captions and user databases are stored as plain files in Backblaze B2 (S3 compatible) and served through Cloudflare CDN. Transfering data from Backblaze to Cloudflare is free due to an agreement between them, and Cloudflare CDN is free which makes this a very cost efficient combination. Backblaze storage cost is 1/2 of Amazon S3, and 1/10 the download fees (outside of Cloudflare), and no upload fees.

## Buckets

Captions, show data, dictionaries and other public data is stored in a public bucket accessible at `https://cdn.lazybug.ai/file/lazybug-public/`. Personal user data, such as the interaction log and user settings are stored in a private bucket at `https://cdn.lazybug.ai/file/lazybug-accounts/`. Other data, which we don't want/need to serve to users is stored in another private bucket.

The accounts bucket, being private cannot be served through the CDN, and therefore we have to pay data fees for when users download their personal database (upload is free). Downloads are $0.01/GB. Downloads should only happen when the user switches clients or logs out/in. 10k downloads per day @ 5MB amounts to $15/month. By the time this becomes expensive we can switch to something more fine-grained than syncing the entire database every time.

## Versioning and Syncing

For captions and other data, we want to keep old versions of the same file in case it's updated but references to it remain elsewhere in user data. We also want to reduce the number of requests and amount of data we pull from Cloudflare (and Backblaze), even if it's free (minimizing waste is the decent thing to do), therefore we want to make files immutable so that Cloudflare doesn't have to keep fetching from Backblaze to see if the data changed.

1. We store a `{filename}.hash` with the SHA256 content hash of the file, and the contents at `{filename}-{hash}.{ext}`
2. When the file changes, we save the new version in a new file with the hash in the filname and update the .hash file to point to it
3. We then upload the new files with the `make push-public` command.
4. We then use the `purge_cache` Cloudflare API to purge the .hash files from the cache, so that clients will download the new one This can be done for all files in `data/remote/public` by calling the `make purge-cloudflare-public` command.

We also cache files in the IndexedDB for lazybug.ai in order to minimize uncessary fetching from Cloudflare as the browser cache can be unreliable.

## User account data

User data is stored in the browser IndexedDB of lazybug.ai and is synced to the private lazybug-accounts bucket on Backblaze via the Python backend. This is done by exporting the database file, calling the `/api/signed-upload-link/{size}` end-point, which will in turn authenticate the user and call the B2 API to get a signed upload link for that user's database file. When the frontend receives this URL, which is valid for a temporary duration, it simply uploads the file directly to it. This avoids having to send the data to our backend first, which saves on bandwidth. The same goes for downloads, but instead using the `api/signed-download-link` endpoint. 

## Dev notes

### Backblaze Settings

Cache header for lazybug-public: `{"cache-control":"max-age=31536000"}`

Update cors rules for lazybug-accounts bucket to allow signed upload/download URLs:
```
b2 update-bucket --corsRules '[{"corsRuleName":"uploadDownloadFromAnyOrigin", "allowedOrigins": [""], "allowedHeaders": [""], "allowedOperations": ["s3_delete", "s3_get", "s3_head", "s3_post", "s3_put"], "maxAgeSeconds": 3600}]' lazybug-accounts allPublic
```

### Cloudflare Settings

1. SSL/TLS mode should be set to Full (strict)
2. SSL/TLS -> Origin Server: The Python backend needs a certificate for serving HTTPS, which can be created/downloaded here
3. SSL/TLS -> Edge Certificates -> Always Use HTTPS (ON)
4. Rules -> Page Rules:
    * `discourse.lazybug.ai/*` | Disable Performance  (https://meta.discourse.org/t/how-do-you-setup-cloudflare/32258/22?page=2)
    * `lazybug.ai/static/*` | Browser Cache TTL: 2 minutes, Cache Level: Cache Everything
    * `cdn.lazybug.ai/file/lazybug-public/*` | Cache Level: Cache Everything

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

# Docker

There is a docker image which contains everything needed to build the frontend and extract captions from videos etc. To download the image run: `docker pull martindbp/lazybug`.

To run a make command (e.g. `frontend`) inside a lazybug container, run `make docker COMMAND=frontend`. This will also map a volume from current directory to the container.
