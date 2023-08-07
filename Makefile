.PHONY: clean
clean:
	rm -rf dataset
	rm -rf texts

.PHONY: dataset
dataset:
	mkdir texts
	mkdir -p dataset/images
	mkdir -p dataset/masks
	node generate_text_images.js
	python generate_dataset.py

.PHONY: test
test:
	python -m unittest discover -s helpers/ -p 'test_*.py'

.PHONY: zip-ext
zip-ext:
	- rm data/remote/public/browser_extension.zip
	cd frontend/dist && zip -r ../../data/remote/public/browser_extension.zip *
	VERSION=$$(grep "\"version\"" frontend/manifest.json | cut -d"\"" -f 4) ; \
	cp -r data/remote/public/browser_extension.zip data/remote/public/browser_extension_$$VERSION.zip

.PHONY: pre-public-sync
pre-public-sync:
	make show-list-full
	make video-list
	#make cedict
	make public-cedict
	#make names-list
	make hsk-words
	make simple-chars
	make strings

.PHONY: push-public
push-public:
	touch synced.txt
	b2 sync --noProgress data/remote/public b2://lazybug-public --skipNewer | tee synced.txt
	make purge-cloudflare-public

.PHONY: push-private
push-private:
	b2 sync data/remote/private b2://lazybug-private --skipNewer

.PHONY: push-raw-captions
push-raw-captions:
	b2 sync data/remote/private/caption_data/raw_captions b2://lazybug-private/caption_data/raw_captions --skipNewer

.PHONY: pull-private-essentials
push-private-essentials:
	b2 sync data/remote/private b2://lazybug-private --skipNewer --excludeRegex '.*caption_data.*'

.PHONY: pull-public
pull-public:
	b2 sync b2://lazybug-public data/remote/public --skipNewer

.PHONY: pull-private
pull-private:
	b2 sync b2://lazybug-private data/remote/private --skipNewer

.PHONY: pull-private-essentials
pull-private-essentials:
	b2 sync b2://lazybug-private data/remote/private --skipNewer --excludeRegex '.*caption_data.*'

.PHONY: pull-public
pull-models:
	b2 sync b2://lazybug-public/models data/remote/public/models --skipNewer
	ln -s data/remote/public/models ~/.cnocr

check-cloudflare-env:
ifndef CLOUDFLARE_ZONE_ID
	$(error CLOUDFLARE_ZONE_ID is undefined)
endif

.PHONY: pull-raw-captions
pull-raw-captions:
	b2 sync b2://lazybug-private/caption_data/raw_captions data/remote/private/caption_data/raw_captions --skipNewer

.PHONY: purge-cloudflare-public
purge-cloudflare-public: check-cloudflare-env
	cat synced.txt | sed -E 's/upload //' | xargs -I{}  curl -X POST "https://api.cloudflare.com/client/v4/zones/$$CLOUDFLARE_ZONE_ID/purge_cache" \
     -H "X-Auth-Email: $$CLOUDFLARE_EMAIL" \
     -H "X-Auth-Key: $$CLOUDFLARE_AUTH_KEY" \
     -H "Content-Type: application/json" \
     -H "Origin: chrome-extension://ackcmdammmejmpannblpninboapjkcgm" \
     --data '{"files":["https://cdn.lazybug.ai/file/lazybug-public/{}"]}'
	echo "Synced" && cat synced.txt && rm synced.txt

.PHONY: pinyin-classifiers
pinyin-classifiers:
	merkl -v run process_show.make_pinyin_db_classifiers

.PHONY: cedict
cedict:
	merkl -v run process_show.make_cedict_db

.PHONY: public-cedict
public-cedict:
	merkl -v run process_show.make_public_cedict_db

.PHONY: names-list
names-list:
	merkl -v run process_show.make_names_list

.PHONY: download-yt
download-yt:
	mkdir -p $(out)/$(show)
	- cat data/git/shows/$(show).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\".*$//\1/g" | xargs -I {} yt-dlp -o "$(out)/$(show)/youtube-%(id)s.%(ext)s" --write-srt --all-subs --default-search "ytsearch" -- {}
	cp $(out)/$(show)/*.vtt data/remote/private/caption_data/translations/

.PHONY: mv-files
mv-files:
	cat data/git/shows/$(show).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\".*$//\1/g" | xargs -I {} echo mv "data/remote/private/caption_data/raw_captions/youtube-{}{.json,-hanzi.json}"


.PHONY: transfer-show-subtitles
transfer-show-subtitles:
	cat data/git/shows/$(from).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\".*$//\1/g" > from_ids.txt
	cat data/git/shows/$(to).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\".*$//\1/g" > to_ids.txt
	# NOTE: use this command from bash, requires `rename` tool from apt
	paste from_ids.txt to_ids.txt | xargs -l bash -c 'rename "s/$0/$1/g" data/remote/public/subtitles/*'


.PHONY: process-show-captions
process-show-captions:
	merkl -v run process_show.process_show_captions ${show} ${videos}

.PHONY: process-translations
process-translations:
	merkl -v run process_show.process_translations ${show}

.PHONY: process-segmentation-alignments
process-segmentation-alignments:
	merkl -v run process_show.process_segmentation_alignment ${show} ${video}

.PHONY: video-list
video-list:
	ls data/remote/public/subtitles/*.hash | xargs -I{} basename {} .hash | python text_list_to_json_array.py > data/remote/public/video_list.json
	LIST_HASH=$$(md5sum data/remote/public/video_list.json | cut -d " " -f1) ; \
	echo $$LIST_HASH > data/remote/public/video_list.hash ; \
	mv data/remote/public/video_list.json "data/remote/public/video_list-$$LIST_HASH.json"

.PHONY: show-list-full
show-list-full:
	python make_discourse_topics.py
	merkl -v run make_shows_list.make_shows_list
	LIST_HASH=$$(md5sum data/remote/public/show_list_full.json | cut -d " " -f1) ; \
	echo $$LIST_HASH > data/remote/public/show_list_full.hash ; \
	mv data/remote/public/show_list_full.json "data/remote/public/show_list_full-$$LIST_HASH.json"
	BLOOM_HASH=$$(md5sum data/remote/public/bloom_filters.json | cut -d " " -f1) ; \
	echo $$BLOOM_HASH > data/remote/public/bloom_filters.hash ; \
	mv data/remote/public/bloom_filters.json "data/remote/public/bloom_filters-$$BLOOM_HASH.json"
	DICT_HASH=$$(md5sum data/remote/public/shows_dictionary.json | cut -d " " -f1) ; \
	echo $$DICT_HASH > data/remote/public/shows_dictionary.hash ; \
	mv data/remote/public/shows_dictionary.json "data/remote/public/shows_dictionary-$$DICT_HASH.json"

.PHONY: show-list
show-list:
	python list_available_shows.py | xargs -I{} basename {} .json | python text_list_to_json_array.py > data/remote/public/show_list.json
	LIST_HASH=$$(md5sum data/remote/public/show_list.json | cut -d " " -f1) ; \
	echo $$LIST_HASH > data/remote/public/show_list.hash ; \
	mv data/remote/public/show_list.json "data/remote/public/show_list-$$LIST_HASH.json"

.PHONY: segmentation-model
segmentation-model:
	merkl -v run train_predict.train_pipeline

.PHONY: finetune-segmentation-model
finetune-segmentation-model:
	merkl -v run train_predict.finetune_pipeline

.PHONY: diff
diff:
	NEXT_FILE=$$(ls -t data/remote/public/subtitles/${id}*.json | head -n 2 | head -1); \
	PREV_FILE=$$(ls -t data/remote/public/subtitles/${id}*.json | head -n 2 | tail -1); \
	vimdiff $$PREV_FILE $$NEXT_FILE

.PHONY: diff-test-cases
diff-test-cases:
	make diff id="youtube-GEKmB3elfTE"
	make diff id="youtube-YtzqsA-a8MM"

.PHONY: test-cases
test-cases:
	make process-segmentation-alignments show=beijingqingnian
	make process-segmentation-alignments show=doutinghao
	make process-segmentation-alignments show=huanlesong

.PHONY: frontend-web
frontend-web:
	vue-cli-service build frontend/components/WebRoot.vue --target lib --dest frontend/dist_components/web
	cp frontend/dist_components/web/*.umd.js frontend/dist/
	-cp frontend/dist_components/web/*.css frontend/dist/
	make frontend-copy

.PHONY: frontend-caption
frontend-caption:
	vue-cli-service build frontend/components/ExtensionCaption.vue --target lib --dest frontend/dist_components/extensioncaption
	cp frontend/dist_components/extensioncaption/*.umd.js frontend/dist/
	-cp frontend/dist_components/extensioncaption/*.css frontend/dist/
	make frontend-copy

.PHONY: frontend-clean
frontend-clean:
	- rm -r frontend/dist
	- rm -r frontend/dist_components
	mkdir -p frontend/dist
	mkdir -p frontend/dist_components
	make css
	make frontend

.PHONY: frontend
frontend:
	make frontend-caption
	make frontend-web

.PHONY: local
local:
	make frontend
	sed -i -E "s/LOCAL = false/LOCAL = true/g" frontend/dist/*.js


.PHONY: frontend-copy
frontend-copy:
	cp frontend/*.js frontend/dist/
	cp frontend/*.html frontend/dist/
	cp frontend/manifest.json frontend/dist/
	cp frontend/deps/* frontend/dist/
	cp frontend/css/* frontend/dist/
	cp -r frontend/images frontend/dist/
	VERSION=$$(grep "\"version\"" frontend/manifest.json | cut -d"\"" -f 4) ; \
	sed -i -E "s/VERSION = null/VERSION = $$VERSION/g" frontend/dist/*.js

.PHONY: release
release:
	sed -i -E "s/DEVMODE = true/DEVMODE = false/g" frontend/dist/*.js
	python make_release_manifest.py frontend/manifest.json > frontend/dist/manifest.json
	rm frontend/dist/deepl_ext.js
	rm frontend/dist/local.html
	make zip-ext

.PHONY: css
css:
	sass frontend/css/lazybugcaption_quasar.sass frontend/dist/lazybugcaption_quasar.css
	sed -i -E "s/\.lazybugcaption (body|html|:root)/\1/g" frontend/dist/lazybugcaption_quasar.css
	sed -i -E "s/rem;/em;/g" frontend/dist/lazybugcaption_quasar.css

.PHONY: hsk-words
hsk-words:
	HSK_WORDS_HASH=$$(md5sum data/git/hsk_words.json | cut -d " " -f1) ; \
	echo $$HSK_WORDS_HASH > data/remote/public/hsk_words.hash ; \
	cp data/git/hsk_words.json "data/remote/public/hsk_words-$$HSK_WORDS_HASH.json"

.PHONY: simple-chars
simple-chars:
	SIMPLE_CHARS_HASH=$$(md5sum data/git/simple_chars.json | cut -d " " -f1) ; \
	echo $$SIMPLE_CHARS_HASH > data/remote/public/simple_chars.hash ; \
	cp data/git/simple_chars.json "data/remote/public/simple_chars-$$SIMPLE_CHARS_HASH.json"

.PHONY: strings
strings:
	STRINGS_HASH=$$(md5sum data/git/strings.json | cut -d " " -f1) ; \
	echo $$STRINGS_HASH > data/remote/public/strings.hash ; \
	cp data/git/strings.json "data/remote/public/strings-$$STRINGS_HASH.json"


check-python-env:
ifndef ENV_PYTHON
	$(error ENV_PYTHON is undefined, set it to your virtualenv python path)
endif

.PHONY: run-server-local
run-server-local: check-python-env
	LOCAL=1 sudo --preserve-env $(ENV_PYTHON) backend/main.py 443

.PHONY: run-server
run-server:
	python backend/main.py

.PHONY: run-server-prod
run-server-prod:
	sudo --preserve-env nohup python backend/main.py 443 &

.PHONY: update-server
update-server:
	git fetch
	git reset --hard origin/master
	make docker-server COMMAND=frontend
	make purge-web-cache
	-make kill-server
	make run-server-prod

.PHONY: purge-web-cache
purge-web-cache: check-cloudflare-env
	ls frontend/dist | xargs -I{}  curl -X POST "https://api.cloudflare.com/client/v4/zones/$$CLOUDFLARE_ZONE_ID/purge_cache" \
     -H "X-Auth-Email: $$CLOUDFLARE_EMAIL" \
     -H "X-Auth-Key: $$CLOUDFLARE_AUTH_KEY" \
     -H "Content-Type: application/json" \
     -H "Origin: chrome-extension://ackcmdammmejmpannblpninboapjkcgm" \
     --data '{"files":["https://lazybug.ai/static/{}"]}'

.PHONY: kill-server
kill-server:
	pgrep -f "python backend/main" | head -n1 | xargs -I{} kill -9 {}

.PHONY: local-ssl-cert
local-ssl-cert:
	mkdir data/local/ssl_cert/ && \
	mkdir data/local/ssl_keys/ && \
	cd data/local/ssl_cert/ && \
	openssl genrsa -out CA.key -des3 2048 && \
	openssl req -x509 -sha256 -new -nodes -days 3650 -key CA.key -out CA.pem && \
	openssl genrsa -out localhost.key -des3 2048 && \
	openssl req -new -key localhost.key -out localhost.csr && \
	openssl x509 -req -in localhost.csr -CA CA.pem -CAkey CA.key -CAcreateserial -days 3650 -sha256 -extfile ../../git/localhost.ext -out localhost.crt && \
	openssl rsa -in localhost.key -out localhost.decrypted.key && \
	cp localhost.crt ../ssl_keys/fullchain.pem && \
	cp localhost.decrypted.key ../ssl_keys/privkey.pem

.PHONY: docker-images
docker-images:
	cp backend/requirements.txt docker/server/
	docker build --rm -t martindbp/lazybug-server docker/server
	cp requirements.txt docker/processing/
	docker build --rm -t martindbp/lazybug-processing docker/processing
	rm docker/server/requirements.txt docker/processing/requirements.txt

.PHONY: docker-push
docker-push:
	docker push martindbp/lazybug-server
	docker push martindbp/lazybug-processing

.PHONY: docker-pull
docker-pull:
	docker pull martindbp/lazybug-server
	docker pull martindbp/lazybug-processing

.PHONY: run-docker-processing-bash
run-docker-processing-bash:
	docker run --volume $$(pwd):/lazybug --workdir /lazybug --rm -it --entrypoint bash martindbp/lazybug-processing

.PHONY: run-docker-server-bash
run-docker-server-bash:
	docker run --volume $$(pwd):/lazybug --workdir /lazybug --rm -it --entrypoint bash martindbp/lazybug-processing

.PHONY: docker-server
docker-server:
	docker run --volume $$(pwd):/lazybug --workdir /lazybug martindbp/lazybug-server make $(COMMAND)

.PHONY: docker-processing
docker-processing:
	docker run --volume $$(pwd):/lazybug --workdir /lazybug martindbp/lazybug-processing make $(COMMAND)
