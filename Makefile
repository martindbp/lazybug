install:
	sudo apt update
	sudo apt install -y libcairo2-dev pkg-config python3.9-dev nodejs npm
	pip install -r requirements.txt
	npm install canvas utfstring
	sudo npm install -g vue@next @vue/cli-service @vue/compiler-sfc @vue/cli-init sass
	# For some reason, some module is trying to import "vue/compiler-sfc" instead of "@vue/compiler-sfc"
	# The hack below works
	ln -s /usr/local/lib/node_modules/@vue /usr/local/lib/node_modules/vue
	browser_extension/dist/

clean:
	rm -rf dataset
	rm -rf texts

dataset:
	mkdir texts
	mkdir -p dataset/images
	mkdir -p dataset/masks
	node generate_text_images.js
	python generate_dataset.py

test:
	python -m unittest discover -s helpers/ -p 'test_*.py'

zip-ext:
	- rm data/remote/public/browser_extension.zip
	cd browser_extension/dist && zip -r ../../data/remote/public/browser_extension.zip *

pre-public-sync:
	make show-list
	make video-list
	make cedict
	make public-cedict
	make names-list

push-public:
	touch synced.txt
	b2 sync --noProgress data/remote/public b2://zimu-public --skipNewer | tee synced.txt
	make purge-cloudflare-public

push-private:
	b2 sync data/remote/private b2://zimu-private --skipNewer

push-private-essentials:
	b2 sync data/remote/private b2://zimu-private --excludeRegex '.*caption_data.*' --skipNewer

pull-public:
	b2 sync b2://zimu-public data/remote/public

pull-private:
	b2 sync b2://zimu-private data/remote/private

pull-private-essentials:
	b2 sync b2://zimu-private data/remote/private --excludeRegex '.*caption_data.*'

check-cloudflare-env:
ifndef CLOUDFLARE_ZONE_ID
	$(error CLOUDFLARE_ZONE_ID is undefined)
endif

.PHONY: purge-cloudflare-public
purge-cloudflare-public: check-cloudflare-env
	cat synced.txt | sed -E 's/upload //' | xargs -I{}  curl -X POST "https://api.cloudflare.com/client/v4/zones/$$CLOUDFLARE_ZONE_ID/purge_cache" \
     -H "X-Auth-Email: $$CLOUDFLARE_EMAIL" \
     -H "X-Auth-Key: $$CLOUDFLARE_AUTH_KEY" \
     -H "Content-Type: application/json" \
     -H "Origin: chrome-extension://ackcmdammmejmpannblpninboapjkcgm" \
     --data '{"files":["https://cdn.zimu.ai/file/zimu-public/{}"]}'
	echo "Synced" && cat synced.txt && rm synced.txt

pinyin-classifiers:
	merkl -v run predict_video.make_pinyin_db_classifiers

cedict:
	merkl -v run predict_video.make_cedict_db

public-cedict:
	merkl -v run predict_video.make_public_cedict_db

names-list:
	merkl -v run predict_video.make_names_list

download-yt:
	mkdir -p $(out)/$(show)
	cat data/remote/public/shows/$(show).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\".*$//\1/g" | xargs -I {} yt-dlp -o "$(out)/$(show)/youtube-%(id)s.%(ext)s" --write-srt --all-subs --default-search "ytsearch" -- {}
	mv $(out)/$(show)/*.vtt data/remote/private/caption_data/translations/

mv-files:
	cat data/remote/public/shows/$(show).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\".*$//\1/g" | xargs -I {} echo mv "data/remote/private/caption_data/raw_captions/youtube-{}{.json,-hanzi.json}"

process-video-captions:
	merkl -v run predict_video.process_video_captions ${show} ${videos}

process-translations:
	merkl -v run predict_video.process_translations ${show} --force-redo

process-segmentation-alignments:
	merkl -v run predict_video.process_segmentation_alignment ${show} ${video}

video-list:
	ls data/remote/public/subtitles/*.hash | xargs -I{} basename {} .hash | python text_list_to_json_array.py > data/remote/public/video_list.json
	LIST_HASH=$$(md5sum data/remote/public/video_list.json | cut -d " " -f1) ; \
	echo $$LIST_HASH > data/remote/public/video_list.hash ; \
	mv data/remote/public/video_list.json "data/remote/public/video_list-$$LIST_HASH.json"

show-list:
	python list_available_shows.py | xargs -I{} basename {} .json | python text_list_to_json_array.py > data/remote/public/show_list.json
	LIST_HASH=$$(md5sum data/remote/public/show_list.json | cut -d " " -f1) ; \
	echo $$LIST_HASH > data/remote/public/show_list.hash ; \
	mv data/remote/public/show_list.json "data/remote/public/show_list-$$LIST_HASH.json"

segmentation-model:
	merkl -v run train_predict.train_pipeline

finetune-segmentation-model:
	merkl -v run train_predict.finetune_pipeline

diff:
	NEXT_FILE=$$(ls -t data/remote/public/subtitles/${id}*.json | head -n 2 | head -1); \
	PREV_FILE=$$(ls -t data/remote/public/subtitles/${id}*.json | head -n 2 | tail -1); \
	vimdiff $$PREV_FILE $$NEXT_FILE

diff-test-cases:
	make diff id="youtube-GEKmB3elfTE"
	make diff id="youtube-YtzqsA-a8MM"

test-cases:
	make process-segmentation-alignments show=beijingqingnian
	make process-segmentation-alignments show=doutinghao
	make process-segmentation-alignments show=huanlesong

ext-caption:
	vue-cli-service build browser_extension/components/CaptionManager.vue --target lib --dest browser_extension/dist_components/captionmanager
	cp browser_extension/dist_components/captionmanager/*.umd.js browser_extension/dist/
	-cp browser_extension/dist_components/captionmanager/*.css browser_extension/dist/
	make ext-copy

ext-popup:
	vue-cli-service build browser_extension/components/PopupRoot.vue --target lib --dest browser_extension/dist_components/popuproot
	cp browser_extension/dist_components/popuproot/*.umd.js browser_extension/dist/
	-cp browser_extension/dist_components/popuproot/*.css browser_extension/dist/
	make ext-copy


ext-dashboard:
	vue-cli-service build browser_extension/components/DashboardRoot.vue --target lib --dest browser_extension/dist_components/dashboardroot
	cp browser_extension/dist_components/dashboardroot/*.umd.js browser_extension/dist/
	-cp browser_extension/dist_components/dashboardroot/*.css browser_extension/dist/
	make ext-copy

ext-clean:
	- rm -r browser_extension/dist
	- rm -r browser_extension/dist_components
	mkdir -p browser_extension/dist
	mkdir -p browser_extension/dist_components
	make css
	make ext

ext:
	make ext-caption
	make ext-popup
	make ext-dashboard

ext-copy:
	cp browser_extension/deepl_main.js browser_extension/dist/
	cp browser_extension/*.js browser_extension/dist/
	cp browser_extension/*.html browser_extension/dist/
	cp browser_extension/manifest.json browser_extension/dist/
	cp browser_extension/deps/* browser_extension/dist/
	cp browser_extension/css/* browser_extension/dist/
	cp -r browser_extension/images browser_extension/dist/

release:
	sed -i -E 's/ZIMUDEVMODE = true/ZIMUDEVMODE = false/g' browser_extension/dist/*.js
	python make_release_manifest.py browser_extension/manifest.json > browser_extension/dist/manifest.json
	rm browser_extension/dist/deepl_main.js
	rm browser_extension/dist/devtools.js
	rm browser_extension/dist/local.html
	make zip-ext

css:
	sass browser_extension/css/zimu_quasar.sass browser_extension/dist/zimu_quasar.css
	sed -i -E 's/\.zimu (body|html|:root)/\1/g' browser_extension/dist/zimu_quasar.css
	sed -i -E 's/rem;/em;/g' browser_extension/dist/zimu_quasar.css

hsk-words:
	HSK_WORDS_HASH=$$(md5sum data/git/hsk_words.json | cut -d " " -f1) ; \
	echo $$HSK_WORDS_HASH > data/remote/public/hsk_words.hash ; \
	cp data/git/hsk_words.json "data/remote/public/hsk_words-$$HSK_WORDS_HASH.json"

logo:
	cp browser_extension/images/logo.svg browser_extension/images/logo_changed.svg
	sed -i -E 's/#f65c40/#1C7287/g' browser_extension/images/logo_changed.svg
	sed -i -E 's/#0f62e4/#db931f/g' browser_extension/images/logo_changed.svg

anki-templates:
	cp anki_templates/cloze_front.js data/remote/public/anki_templates/cloze_word_py_hz_front.js
	cp anki_templates/cloze_front.js data/remote/public/anki_templates/cloze_word_tr_front.js
	cp anki_templates/cloze_front.js data/remote/public/anki_templates/cloze_word_all_front.js
	cp anki_templates/cloze_front.js data/remote/public/anki_templates/cloze_translation_front.js
	cp anki_templates/basic_front.js data/remote/public/anki_templates/basic_py_hz_front.js
	cp anki_templates/basic_front.js data/remote/public/anki_templates/basic_tr_front.js
	cp anki_templates/basic_front.js data/remote/public/anki_templates/basic_hz_front.js
	cp anki_templates/basic_back.js data/remote/public/anki_templates/basic_py_hz_back.js
	cp anki_templates/basic_back.js data/remote/public/anki_templates/basic_tr_back.js
	cp anki_templates/basic_back.js data/remote/public/anki_templates/basic_hz_back.js
	sed -i -E 's/CLOZE_TYPE/cloze_word_py_hz/g' data/remote/public/anki_templates/cloze_word_py_hz_front.js
	sed -i -E 's/CLOZE_TYPE/cloze_word_tr/g' data/remote/public/anki_templates/cloze_word_tr_front.js
	sed -i -E 's/CLOZE_TYPE/cloze_word_all/g' data/remote/public/anki_templates/cloze_word_all_front.js
	sed -i -E 's/CLOZE_TYPE/cloze_translation/g' data/remote/public/anki_templates/cloze_translation_front.js
	sed -i -E 's/CLOZE_TYPE/basic_py_hz/g' data/remote/public/anki_templates/basic_py_hz_*.js 
	sed -i -E 's/CLOZE_TYPE/basic_tr/g' data/remote/public/anki_templates/basic_tr_*.js 
	sed -i -E 's/CLOZE_TYPE/basic_hz/g' data/remote/public/anki_templates/basic_hz_*.js 
