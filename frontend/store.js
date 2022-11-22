const BLOOM_FILTER_N = 287552;
const BLOOM_FILTER_K = 13;
const DEFAULT_FONT_SIZE = 24;
const DEFAULT_SHORTCUTS = {
    next: 'ArrowRight',
    prev: 'ArrowLeft',
    replay: 'KeyR',
    dictionary: 'KeyD',
    peek: 'KeyP',
    peekFullTr: 'KeyT',
    peekPy: 'KeyY',
    peekHz: 'KeyH',
    peekTr: 'KeyN',
    pausePlay: 'Space', // already a shortcut, but is applied outside the video in Web
}


function syncOptions(state) {
    setIndexedDbData('other', ['options'], [state.options], function() {});
}

function getShowInfo(store, state = null) {
    if (state === null) state = store.state;
    if ([null, undefined].includes(state.captionData) || [null, undefined].includes(state.showList)) return null;

    return state.showList[state.captionData.show_name];
}

const store = new Vuex.Store({
    state: {
        extensionOn: true,
        accessToken: getCookie('jwt'),
        accountEmail: getCookie('email'),
        captionId: null,
        captionDocked: localStorage.getItem('captionDocked') === 'true',
        videoId: null,
        AVElement: null,
        videoAPI: null,
        videoDuration: null,
        sessionTime: null,
        captionData: null,
        captionHash: null, // use this for event log. Equals 'fetching' if in the process of fetching
        fetchedCaptionId: null,
        resourceFetchErrors: [],
        youtubeAPIReady: LOCAL_ONLY, // if local only we don't use youtube, so set to true
        showList: null,
        showBloomFilters: null,
        thumbnailObserver: null,
        videoList: null,
        DICT: null,
        HSK_WORDS: null,
        SIMPLE_CHARS: null,
        STRINGS: null,
        states: Vue.ref({}),
        bloomFilter: null,
        captionFontScale: 0.5,
        captionFontSize: 24,
        captionOffset: [0, 0],
        isMovingCaption: false,
        showDialog: Vue.ref({
            options: false,
            account: false, // false, 'register' or 'login'
            dictionary: false,
            devtools: false,
            sync: false,
            embeddable: false,
        }),
        peekStates: Vue.ref({
            py: [],
            hz: [],
            tr: [],
            rows: {
                py: false,
                tr: false,
                hz: false,
                translation: false,
            }
        }),
        autoPeekStates: Vue.ref({
            py: [],
            hz: [],
            tr: [],
            rows: {
                py: false,
                tr: false,
                hz: false,
                translation: false,
            }
        }),
        optionsHighlightSection: null,
        showDictionaryRange: [-1, -1],
        timingOffset: 0,
        page: 'content',
        playingShowId: null,
        playingSeason: null,
        playingEpisode: null,
        showSyncDialog: false,
        lastSyncDate: localStorage.getItem('lastSyncDate'),
        needSync: localStorage.getItem('needSync', 'false') === 'true',
        isSyncing: false,
        syncProgress: [],
        syncError: null,
        options: Vue.ref({
            autoPause: false,
            WPSThreshold: 2.0,
            characterSet: 'sm',
            blurCaptions: true,
            pin: {
                hz: false,
                py: false,
                tr: false,
                translation: false,
            },
            pinLevels: {
                hz: 0,
                py: 0,
                tr: 0,
                translation: 0,
            },
            displayTranslation: 0, // index into [human, machine][min(idx, length)]
            hideWordsLevel: 0,
            peekAfterAutoHide: true,
            keyboardShortcutsToggle: true,
            keyboardShortcuts: DEFAULT_SHORTCUTS,
            anki: {
                advancedCards: [
                    "Cloze word hanzi + pinyin",
                    "Cloze word translation",
                    "Cloze whole word",
                    "Basic produce Chinese",
                    "Basic produce translation",
                    "Basic produce Hanzi",
                ],
                advancedToggled: [
                    false,
                    false,
                    false,
                    false,
                    false,
                    false,
                ],
                basicToggled: [
                    false,
                    false,
                    false,
                ],
                clozeIncludeHint: false,
            },
        }),
    },
    mutations: {
        setExtensionOn(state, val) {
            state.extensionOn = val;
        },
        setNeedSync(state, val) {
            state.needSync = val;
            localStorage.setItem('needSync', val);
        },
        setCaptionDocked(state, val) {
            state.captionDocked = val;
            localStorage.setItem('captionDocked', val);
        },
        setIsSyncing(state, val) {
            state.isSyncing = val;
        },
        setSyncError(state, val) {
            state.syncError = val;
        },
        setLastSyncDate(state, val) {
            state.lastSyncDate = val;
            state.needSync = false;
            localStorage.setItem('needSync', false);
            localStorage.setItem('lastSyncDate', val);
        },
        addSyncProgress(state, val) {
            state.syncProgress.push(val);
        },
        setSyncProgress(state, val) {
            state.syncProgress = val;
        },
        setLogin(state, val) {
            state.accessToken = val.accessToken;
            state.accountEmail = val.email;
            state.needSync = true;
            setCookie('jwt', val.accessToken, 365);
            setCookie('email', val.email, 365);
        },
        setLogout(state) {
            state.accessToken = null;
            state.accountEmail = null;
            eraseCookie('jwt');
            eraseCookie('email');
        },
        setNonEmbeddableVideoSelected(state, val) {
            state.nonEmbeddableVideoSelected = val;
        },
        setPlayingShowId(state, val) {
            state.playingShowId = val;
        },
        setPlayingSeason(state, season) {
            state.playingSeason = season;
        },
        setPlayingEpisode(state, episode) {
            state.playingEpisode = episode;
        },
        setVideoAPI(state, api) {
            state.videoAPI = api;
        },
        setAVElement(state, el) {
            state.AVElement = el;
        },
        setVideoDuration(state, duration) {
            state.videoDuration = duration;
        },
        setYoutubeAPIReady(state) {
            state.youtubeAPIReady = true;
        },
        switchTranslation(state) {
            state.options.displayTranslation = (state.options.displayTranslation + 1) % 2;
        },
        setOptionsHighlightSection(state, val) {
            state.optionsHighlightSection = val;
        },
        setVideoId(state, val) {
            state.videoId = val
        },
        setVideoList(state, val) {
            state.videoList = new Set(val);
            if (BROWSER_EXTENSION) {
                const newThumbnailObserver = initializeThumbnailBadges(state.videoList);
                if (state.thumbnailObserver) state.thumbnailObserver.disconnect();
                state.thumbnailObserver = newThumbnailObserver;
            }
        },
        setShowList(state, val) {
            // Add the showId to each show value
            for (const key of Object.keys(val)) {
                val[key].showId = key;
            }
            state.showList = val;
        },
        setSimpleCharsList(state, val) {
            state.SIMPLE_CHARS = val;
            state.bloomFilter = createBloomFilter(state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setStringsList(state, val) {
            state.STRINGS = val;
        },
        resetResourceFetchError(state, val) {
            // We only reset it if the currente error holds this resource type
            // (not some other resource)
            if (state.resourceFetchErrors.includes(val)) {
                state.resourceFetchErrors.splice(state.resourceFetchErrors.indexOf(val), 1);
            }
        },
        setResourceFetchError(state, val) {
            state.resourceFetchErrors.push(val);
        },
        setIsMovingCaption(state, val) {
            state.isMovingCaption = val;
        },
        setTimingOffset(state, val) {
            state.timingOffset = val;
        },
        setCaptionId(state, val) {
            state.captionId = val;
            state.sessionTime = Date.now();
            if ([null, undefined].includes(val)) return;
        },
        setCaptionIdDataHash(state, val) {
            state.captionData = val.data;
            state.captionHash = val.hash;
            state.fetchedCaptionId = val.id;
        },
        setShowDialog(state, val) {
            state.showDialog[val.dialog] = val.val;
        },
        setShowDictionary(state, val) {
            if (! [null, undefined].includes(val.val)) state.showDialog.dictionary = val.val;
            if (val.range) {
                state.showDictionaryRange = val.range;
                if (val.range[0] >= 0) {
                    appendSessionLog(
                        state,
                        [eventsMap['EVENT_SHOW_DICTIONARY_RANGE'], val.range[0], val.range[1]]
                    );
                }
            }
        },
        setStates(state, states) {
            state.states = states;
            state.bloomFilter = createBloomFilter(state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setBloomFilters(state, filters) {
            for (const key of Object.keys(filters.shows)) {
                const bloom = new BloomFilter(BLOOM_FILTER_N, BLOOM_FILTER_K);
                bloom.fromHexString(filters.shows[key].bloom);
                filters.shows[key].bloom = bloom;
            }
            state.showBloomFilters = filters;
        },
        increaseCaptionFontScale(state) {
            state.captionFontScale = Math.min(state.captionFontScale + 0.1, 1.0);
            state.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * state.captionFontScale);
        },
        decreaseCaptionFontScale(state) {
            state.captionFontScale = Math.max(state.captionFontScale - 0.1, 0.3);
            state.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * state.captionFontScale);
        },
        setCaptionOffset(state, offset) {
            state.captionOffset = offset;
        },
        setPeekState(state, val) {
            const states = val.auto ? state.autoPeekStates : state.peekStates;
            if ([undefined, null].includes(val.i)) {
                if (val.type === 'translation') {
                    states[val.type] = true;
                    states.rows[val.type] = true;
                }
                else {
                    states.rows[val.type] = true;
                    // Set peek state for all words
                    for (let i = 0; i < states[val.type].length; i++) {
                        states[val.type][i] = true;
                    }
                }
            }
            else {
                states[val.type][val.i] = true;
            }
        },
        resetPeekStates(state, val) {
            state.peekStates = {
                py: [],
                hz: [],
                tr: [],
                translation: false,
                rows: {
                    hz: false,
                    tr: false,
                    py: false,
                    translation: false,
                },
            };
            for (let i = 0; i < val; i++) {
                for (const type of ['py', 'hz', 'tr']) {
                    state.peekStates[type].push(false);
                }
            }
            state.autoPeekStates = JSON.parse(JSON.stringify(state.peekStates));
        },
        setPeekStates(state, val) {
            state.peekStates = val;
        },
        setBlur(state, val) {
            state.options.blurCaptions = val;
            syncOptions(state);
            appendSessionLog(this, [eventsMap['EVENT_BLUR'], val]);
        },
        setOptions(state, options) {
            state.options = options;
            syncOptions(state);
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
            syncOptions(state);
            if (option.key === 'hideWordsLevel') {
                state.bloomFilter = createBloomFilter(state, BLOOM_FILTER_N, BLOOM_FILTER_K);
            }
        },
        setDeepOption(state, option) {
            state.options[option.key][option.key2] = option.value;
            syncOptions(state);
        },
        setDict(state, dict) {
            state.DICT = dict;
            state.bloomFilter = createBloomFilter(state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setHskWords(state, words) {
            state.HSK_WORDS = words;
            state.bloomFilter = createBloomFilter(state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setAnkiAdvancedCards(state, val) {
            state.options.anki.advancedCards = val;
            syncOptions(state);
        },
        setAnkiCardsAdvancedToggled(state, val) {
            state.options.anki.advancedToggled = val;
            syncOptions(state);
        },
        setAnkiCardsBasicToggled(state, val) {
            state.options.anki.basicToggled = val;
            syncOptions(state);
        },
        setAnkiCardsClozeIncludeHint(state, val) {
            state.options.anki.clozeIncludeHint = val;
            syncOptions(state);
        },
        setPage(state, val) {
            let url = '/' + val;
            if (val === 'player') {
                url += `/${state.playingShowId}/${state.playingSeason + 1}/${state.playingEpisode + 1}`;
            }
            window.history.pushState(null, '', url);
            state.page = val;
        },
        setLocation(state, val) {
            //
            // Routing logic
            //
            const parts = val.pathname.split('/').filter((s) => s.length > 0);
            if (parts.length === 0) state.page = 'content'; // default
            else state.page = parts[0];

            if (parts[0] === 'player') {
                const showId = parts[1];
                state.playingShowId = showId;

                if (parts.length >= 4) {
                    // Pattern: player/show/season/episode/(caption)
                    const seasonIdx = parseInt(parts[2]) - 1;
                    const episodeIdx = parseInt(parts[3]) - 1;
                    if (parts.length === 5) {
                        const captionIdx = parseInt(parts[4]) - 1;
                        state.playingCaptionIdx = captionIdx;
                    }
                    state.playingSeason = seasonIdx;
                    state.playingEpisode = episodeIdx;
                }
                else if (parts.length === 2) {
                    // Pattern: player/movie/
                    state.playingSeason = 0;
                    state.playingEpisode = 0;
                }
                else if (parts.length === 3) {
                    // Pattern: player/movie/caption
                    const captionIdx = parseInt(parts[2]) - 1;
                    state.playingCaptionIdx = captionIdx;
                    state.playingSeason = 0;
                    state.playingEpisode = 0;
                }
            }
        },
    },
});

if (BROWSER_EXTENSION) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'extensionOn') {
            // Reset captionOffset so we have a way get out of the situation where it's outside the window
            store.commit('setCaptionOffset', [0, 0]);
            store.commit('setExtensionOn', message.data);
        }
    });

    chrome.storage.local.get("extensionOn", function(data) {
        store.commit('setExtensionOn', data.extensionOn);
    });
}

const FETCH_PUBLIC_RESOURCES = [
    ['strings.json', 'strings', 'setStringsList'],
    ['public_cedict.json', 'dictionary', 'setDict'],
    ['hsk_words.json', 'HSK word list', 'setHskWords'],
    ['video_list.json', 'video list', 'setVideoList'],
    ['show_list_full.json', 'show list', 'setShowList'],
    ['simple_chars.json', 'simple chars list', 'setSimpleCharsList'],
];


function fetchInitialResources() {
    for (const [filename, errorName, mutation] of FETCH_PUBLIC_RESOURCES) {
        fetchVersionedResource(filename, function (data) {
            if (data === 'error') {
                store.commit('setResourceFetchError', errorName);
            }
            else {
                store.commit('resetResourceFetchError', errorName);
                store.commit(mutation, data);
            }
        });
    }

    fetchPersonalDataToStore(store);
}

if (BROWSER_EXTENSION) {
    // We have to wait for the iframe to load before we can fetch stuff from it
    lazybugIframe.addEventListener('load', fetchInitialResources);
}
else {
    FETCH_PUBLIC_RESOURCES.push(['bloom_filters.json', 'show bloom filters', 'setBloomFilters']);
    fetchInitialResources();

    store.commit('setLocation', document.location); // initial
    window.onpopstate = (event) => {
        store.commit('setLocation', document.location);
    }
}

function addBadge($img, videoList) {
    if ($img === null) return;
    const $a = $img.closest("#thumbnail");
    const youtubeIdRegex = /^.*\?v\=([a-zA-Z0-9_-]*)&?.*/;
    const match = youtubeIdRegex.exec($a.href);
    if (!match) return;

    const id = match[1];
    if (! videoList.has(`youtube-${id}`)) {
        return;
    }

    $img.style.position = 'relative';
    const badge = document.createElement('img');
    badge.classList.add('lazybugbadge');
    badge.src = CDN_URL + 'lazybug-public/images/64_lazybug.png';
    badge.style.filter = 'drop-shadow(5px 5px 5px black)';
    badge.style.width = badge.style.height = '28px';
    badge.style.position = 'absolute';
    badge.style.top = '4px';
    badge.style.left = '4px';
    $img.parentNode.appendChild(badge);
}

function initializeThumbnailBadges(videoList) {
    if (getCurrentSite() === 'youtube') return null;

    for (const $img of document.querySelectorAll('#thumbnail img:not(.lazybugbadge)')) {
        addBadge($img, videoList);
    }

    return new MutationObserver((mutations) => {
        let hasNewThumbnails = false;
        for (let mutation of mutations) {
            switch(mutation.type) {
                case 'childList':
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType !== 1) continue;
                        if (node.tagName === 'IMG' && !node.classList.contains('lazybugbadge') && node.closest('#thumbnail')) {
                            addBadge(node, videoList);
                        }
                        else if (node.id === 'thumbnail') {
                            addBadge(node.querySelector('img:not(.lazybugbadge)'), videoList);
                        }
                    }
                    break;
                case 'attributes':
                    if (mutation.target.id === 'thumbnail' && mutation.attributeName === 'href' && mutation.oldValue !== null) {
                        const $img = mutation.target.querySelector('img:not(.lazybugbadge)');
                        for (const $badgeImg of mutation.target.querySelectorAll('img.lazybugbadge')) {
                            $badgeImg.remove();
                        }
                        addBadge($img, videoList);
                    }
                    break;
            }
        }
    }).observe(document, {subtree: true, childList: true, attributes: true, attributeOldValue: true});
}
