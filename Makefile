install:
	sudo apt install -y libcairo2-dev pkg-config python3.9-dev nodejs npm
	pip install pycairo pangocairocffi
	npm install canvas utfstring

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
	zip -r data/remote/public/browser_extension.zip browser_extension/

pre-public-sync:
	make show-list
	make cedict
	make public-cedict
	make names-list

sync-up-public:
	touch synced.txt
	b2 sync --noProgress data/remote/public b2://zimu-public | tee synced.txt
	make purge-cloudflare-public

sync-up-private:
	b2 sync data/remote/private b2://zimu-private

sync-down-public:
	b2 sync b2://zimu-public data/remote/public

sync-down-private:
	b2 sync b2://zimu-private data/remote/private

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

cedict:
	merkl -v run predict_video.make_cedict_db

public-cedict:
	merkl -v run predict_video.make_public_cedict_db

names-list:
	merkl -v run predict_video.make_names_list

download-yt:
	mkdir -p $(out)/$(show)
	cat data/remote/private/shows/$(show).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\"/\1/g" | xargs -I {} yt-dlp -o "../videos/$(show)/youtube-%(id)s.%(ext)s" --write-srt --all-subs -- {}
	mv ../videos/$(show)/*.vtt data/remote/private/caption_data/translations/

process-video-captions:
	merkl -v run predict_video.process_video_captions ${show} ${videos}

process-translations:
	merkl -v run predict_video.process_translations ${show} --force-redo

process-segmentation-alignments:
	merkl -v run predict_video.process_segmentation_alignment ${show} ${video}

show-list:
	ls data/remote/public/subtitles/*.hash | xargs -I{} basename {} .hash | python text_list_to_json_array.py > data/remote/public/show_list.json 
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

ext:
	mv browser_extension/dist/zimu_quasar.css browser_extension/
	vue-cli-service build browser_extension/components/CaptionManager.vue --target lib --dest browser_extension/dist_captionmanager
	vue-cli-service build browser_extension/components/PopupRoot.vue --target lib --dest browser_extension/dist_popuproot
	mv browser_extension/dist_captionmanager/* browser_extension/dist/
	mv browser_extension/dist_popuproot/* browser_extension/dist/
	mv browser_extension/zimu_quasar.css browser_extension/dist/
	cp browser_extension/deepl_main.js browser_extension/dist/

release:
	sed -i -E 's/ZIMUDEVMODE = true/ZIMUDEVMODE = false/g' browser_extension/dist/*.js

css:
	sass browser_extension/css/zimu_quasar.sass browser_extension/dist/zimu_quasar.css
	sed -i -E 's/\.zimu (body|html|:root)/\1/g' browser_extension/dist/zimu_quasar.css
	sed -i -E 's/rem;/em;/g' browser_extension/dist/zimu_quasar.css

hsk-words:
	HSK_WORDS_HASH=$$(md5sum data/remote/public/hsk_words.json | cut -d " " -f1) ; \
	echo $$HSK_WORDS_HASH > data/remote/public/hsk_words.hash ; \
	mv data/remote/public/hsk_words.json "data/remote/public/hsk_words-$$HSK_WORDS_HASH.json"
