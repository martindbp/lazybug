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

sync-up-public:
	touch synced.txt
	b2 sync data/remote/public b2://zimu-public | tee synced.txt
	make purge-cloudflare

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
     --data '{"files":["https://{}"]}'
	echo "Synced" && cat synced.txt && rm synced.txt

cedict:
	merkl -v run predict_video.make_cedict_db

download-yt:
	mkdir -p $(out)/$(show)
	cat data/remote/private/backup/shows/$(show).json | grep "\"id\"" | sed -E "s/.*: \"youtube-(.*)\"/\1/g" | xargs -I {} yt-dlp -o "$(out)/$(show)/youtube-%(id)s.%(ext)s" --write-srt --sub-lang en -- {}

process-show:
	merkl -v run predict_video.process_show ${show} ${videos}

process-translations:
	merkl -v run predict_video.process_translations ${show}

process-segmentation-alignments:
	merkl -v run predict_video.process_segmentation_alignment ${show} ${video}

show-list:
	ls data/remote/public/subtitles/*.hash | xargs -I{} basename {} .hash | python text_list_to_json_array.py > data/remote/public/show_list.json 
	LIST_HASH=$$(md5sum data/remote/public/show_list.json | cut -d " " -f1) ; \
	echo $$LIST_HASH > data/remote/public/show_list.hash ; \
	mv data/remote/public/show_list.json "data/remote/public/show_list-$$LIST_HASH.json"

segmentation-model:
	merkl run train_predict.train_pipeline

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
	vue-cli-service build browser_extension/components/CaptionManager.vue --target lib --dest browser_extension/dist
	mv browser_extension/zimu_quasar.css browser_extension/dist/

css:
	sass browser_extension/css/zimu_quasar.sass browser_extension/dist/zimu_quasar.css
	sed -i -E 's/\.zimu (body|html|:root)/\1/g' browser_extension/dist/zimu_quasar.css
	sed -i -E 's/rem;/em;/g' browser_extension/dist/zimu_quasar.css

hsk-words:
	HSK_WORDS_HASH=$$(md5sum data/remote/public/hsk_words.json | cut -d " " -f1) ; \
	echo $$HSK_WORDS_HASH > data/remote/public/hsk_words.hash ; \
	mv data/remote/public/hsk_words.json "data/remote/public/hsk_words-$$HSK_WORDS_HASH.json"
