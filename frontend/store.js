const BLOOM_FILTER_N = 287552;
const BLOOM_FILTER_K = 13;
const DEFAULT_FONT_SIZE = 35;
const DEFAULT_EXERCISES_KNOWN_THRESHOLD = 3;
const DEFAULT_PY_EXERCISE_DISTANCE_THRESHOLD = 1.0;
const DEFAULT_TR_EXERCISE_DISTANCE_RATIO_THRESHOLD = 0.15;
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

const OPTIONS_DEFAULT = {
    referrer: document.referrer, // store this to see where user came from when registering
    okReceiveEmails: true,
    doneIntro: localStorage.getItem('doneIntro', 'false') === 'true',
    useSmartSubtitles: true,
    autoPause: 'off', // 'off', 'basic' or 'WPS'
    exercisesOn: true,
    exercisesKnownThreshold: DEFAULT_EXERCISES_KNOWN_THRESHOLD,
    pyExerciseDistanceThreshold: DEFAULT_PY_EXERCISE_DISTANCE_THRESHOLD,
    trExerciseDistanceRatioThreshold: DEFAULT_TR_EXERCISE_DISTANCE_RATIO_THRESHOLD,
    personalExerciseTranslations: {},
    personalKnownVocabulary: [],
    seenTooltips: {
        pinyin: false,
        grading: false,
        finalHelp: false,
    },
    WPSThreshold: 2.0,
    characterSet: 'sm',
    blurCaptions: true,
    pin: {
        hz: false,
        py: false,
        tr: false,
        translation: false,
    },
    show: {
        hz: true,
        py: true,
        tr: true,
        translation: true,
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
};

const syncOptionsDebounced = debounce((state) => syncOptions(state));

function getShowInfo(playerId, store, state = null) {
    if (state === null) state = store.state;
    if (
        (
            isNone(state.playerData[playerId].showId) &&
            isNone(state.playerData[playerId].captionData)
        ) || isNone(state.showList)
    ) return null;

    return state.showList[state.playerData[playerId].showId || state.playerData[playerId].captionData.show_name];
}

// For persisting IndexedDB (see https://dexie.org/docs/StorageManager)
async function persist() {
    return await navigator.storage && navigator.storage.persist &&
        navigator.storage.persist();
}

async function isStoragePersisted() {
    return await navigator.storage && navigator.storage.persisted &&
        navigator.storage.persisted();
}

store = new Vuex.Store({
    state: {
        cssLoaded: false,
        hasLazybugExtension: false,
        fetchedAllPublicResources: false,
        url: null,
        isExtension: BROWSER_EXTENSION,
        isLocal: LOCAL,
        extensionOn: true,
        loggedInThisSession: false, // used to add an iframe to Discourse to automatically log in there
        accessToken: getCookie('jwt'),
        accountEmail: getCookie('email'),
        captionDocked: ['true', null].includes(localStorage.getItem('captionDocked')) && ! BROWSER_EXTENSION,
        localVideoHash: null,
        youtubeAPIReady: LOCAL, // if local only we don't use youtube, so set to true
        showList: null,
        showBloomFilters: null, // only for web app
        thumbnailObserver: null, // only for browser extension
        videoList: null, // only for browser extension
        discourseCommentsForShow: null,
        DICT: null,
        SHOWS_DICTIONARY: {},
        HSK_WORDS: null,
        SIMPLE_CHARS: null,
        STRINGS: null,
        states: Vue.ref({}),
        bloomFilter: null, // bloom filter for known vocab, only for web app
        captionFontScale: 0.5,
        captionFontSize: DEFAULT_FONT_SIZE,
        captionOffset: [0, 0],
        isMovingCaption: false,
        showDialog: Vue.ref({
            options: false,
            account: false, // false, 'register' or 'login'
            dictionary: false,
            devtools: false,
            sync: false,
            embeddable: false,
            intro: false,
        }),
        showTooltip: Vue.ref({
            options: false,
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
        reviewCaptionsList: [],
        reviewCaptionIdIndices: {},
        showDictionaryRange: [-1, -1],
        timingOffset: 0,
        page: 'content',
        lastSyncDate: localStorage.getItem('lastSyncDate'),
        needSync: localStorage.getItem('needSync', 'false') === 'true',
        isSyncing: false,
        syncProgress: [],
        syncError: null,
        options: Vue.ref(OPTIONS_DEFAULT),

        resourceFetchErrors: [],
        // Player data for each session, both for regular viewing and review
        playerData: Vue.ref({
            //playerId: {
                //AVElement: null,
                //videoAPI: null,
                //videoDuration: null,
                //sessionTime: null,?
                //submittedExercises
                //captionId: null, // captionId of the currently viewed video
                //captionData: null,
                //captionHash: null, // use this for event log. Equals 'fetching' if in the process of fetching
                //showId: null,
                //season: null,
                //episode: null,
                //captionIdx: null,
                //navigateToCaptionIdx: null,
            //}
        }),
    },
    mutations: {
        setReviewCaptions(state, val) {
            state.reviewCaptionsList = val.list;
            state.reviewCaptionIdIndices = val.indices;
        },
        setHasLazybugExtension(state) {
            state.hasLazybugExtension = true;
        },
        setCloseAllDialogs(state) {
            for (const key of Object.keys(state.showDialog)) {
                state.showDialog[key] = false;
            }
        },
        setBloomFilter(state, val) {
            state.bloomFilter = val;
        },
        setFetchedAllPublicResources(state) {
            state.fetchedAllPublicResources = true;
        },
        setCssLoaded(state) {
            state.cssLoaded = true;
        },
        setShowDiscourseComments(state, val) {
            state.discourseCommentsForShow = val;
        },
        setLocalVideoHash(state, val) {
            state.localVideoHash = val;
        },
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
        setSyncDone(state, error) {
            state.isSyncing = false;
            state.needSync = false;
            state.syncError = error;
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
            if (val === null) localStorage.removeItem('lastSyncDate');
            else localStorage.setItem('lastSyncDate', val);
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
            state.loggedInThisSession = true;
            setCookie('jwt', val.accessToken, 365);
            setCookie('email', val.email, 365);
        },
        setLoggedOut(state) {
            state.accessToken = null;
            state.accountEmail = null;
            eraseCookie('jwt');
            eraseCookie('email');
            // Reset everything that is tied to the previous logged in user
            this.commit('setLastSyncDate', null);
            this.commit('setOptions', JSON.parse(JSON.stringify(OPTIONS_DEFAULT)));
            this.commit('setStates', {});
            state.playerData = {};
        },
        setNonEmbeddableVideoSelected(state, val) {
            state.nonEmbeddableVideoSelected = val;
        },
        resetPlayerData(state, playerId) {
            if (!state.playerData[playerId]) {
                state.playerData[playerId] = {};
            }
            const playerData = state.playerData[playerId];
            playerData.captionId = null;
            playerData.sessionTime = null;
            playerData.lastCaptionIdx = null;
            playerData.submittedExercises = null;
            playerData.lastCaptionIdx = null;
            playerData.showId = null;
            playerData.season = null;
            playerData.episode = null;
            playerData.navigateToCaptionIdx = null;
            playerData.captionData = null;
            playerData.captionHash = null;
        },
        setPlayerData(state, val) {
            if (!state.playerData[val.playerId]) {
                state.playerData[val.playerId] = {};
            }
            for (const key of Object.keys(val)) {
                if (key === 'playerId') continue;
                state.playerData[val.playerId][key] = val[key];
            }
        },
        setYoutubeAPIReady(state) {
            state.youtubeAPIReady = true;
        },
        switchTranslation(state) {
            state.options.displayTranslation = (state.options.displayTranslation + 1) % 2;
        },
        setVideoList(state, val) {
            state.videoList = new Set(val);
        },
        setShowList(state, val) {
            // Add the showId to each show value
            for (const key of Object.keys(val)) {
                val[key].showId = key;
            }
            state.showList = val;
            this.commit('setURL', state.url); // in case this was loaded after URL
        },
        setSimpleCharsList(state, val) {
            state.SIMPLE_CHARS = val;
            createSetBloomFilterDebounced(this, state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setStringsList(state, val) {
            state.STRINGS = val;
            if (BROWSER_EXTENSION) {
                this.commit('setURL', state.url); // in case this was loaded after URL
            }
        },
        resetResourceFetchError(state, val) {
            // We only reset it if the current error holds this resource type
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
            const prev = state.playerData[val.playerId] ? state.playerData[val.playerId].captionId : null;
            if (prev === val.value) return;
            if (! state.playerData[val.playerId]) {
                state.playerData[val.playerId] = {};
            }
            const playerData = state.playerData[val.playerId];
            playerData.captionId = val.value;
            playerData.sessionTime = Date.now();
            playerData.lastCaptionIdx = 0;
            playerData.submittedExercises = {};
            playerData.lastCaptionIdx = 0;
            if (BROWSER_EXTENSION && prev === null) {
                this.commit('setURL', state.url); // in case this was loaded after URL
            }
        },
        setCaptionIdDataHash(state, val) {
            const playerData = state.playerData[val.playerId];
            if (val.data && playerData.reviewCaptionIndices) {
                val.data.lines = val.data.lines.filter((line, index, arr) => {
                    if (line.length == 9) line.push(undefined); // lineTimingOffset
                    line.push(index);
                    return playerData.reviewCaptionIndices.includes(index);
                });
            }

            playerData.captionData = val.data;
            playerData.captionHash = val.hash;
            if (! isNone(playerData.captionData)) {
                playerData.showId = playerData.captionData.show_name;
                const showInfo = getShowInfo(val.playerId, this);
                let [seasonIdx, episodeIdx] = findVideoInShowInfo(showInfo, playerData.captionId);
                playerData.season = seasonIdx;
                playerData.episode = episodeIdx;
            }
            playerData.lastCaptionIdx = 0;
            if (BROWSER_EXTENSION) {
                this.commit('setURL', state.url); // in case this was loaded after URL
            }
        },
        setShowDialog(state, val) {
            state.showDialog[val.dialog] = val.value;
        },
        setShowDictionary(state, val) {
            if (! isNone(val.value)) state.showDialog.dictionary = val.value;
            if (val.range) {
                state.showDictionaryRange = val.range;
                if (val.range[0] >= 0) {
                    appendSessionLog(
                        val.playerId,
                        this,
                        [eventsMap['EVENT_SHOW_DICTIONARY_RANGE'], val.range[0], val.range[1]]
                    );
                }
            }
        },
        setStates(state, states) {
            state.states = states;
            createSetBloomFilterDebounced(this, state, BLOOM_FILTER_N, BLOOM_FILTER_K);
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
            console.assert([true, false, 'temporaryPeek', 'hiddenAfterTemporaryPeek'].includes(val.value));
            if (isNone(val.i)) {
                if (val.type === 'translation') {
                    state.peekStates[val.type] = val.value;
                    state.peekStates.rows[val.type] = val.value;
                }
                else {
                    state.peekStates.rows[val.type] = val.value;
                }
            }
            else {
                state.peekStates[val.type][val.i] = val.value;
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
                for (const type of STATE_ORDER) {
                    state.peekStates[type].push(false);
                }
            }
        },
        setPeekStates(state, val) {
            state.peekStates = val;
        },
        setBlur(state, val) {
            state.options.blurCaptions = val;
            syncOptionsDebounced(state);
            appendSessionLog('player', this, [eventsMap['EVENT_BLUR'], val]);
        },
        setOptions(state, options) {
            state.options = options;
            syncOptionsDebounced(state);
            this.commit('setNeedSync', true);
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
            syncOptionsDebounced(state);
            if (option.key === 'hideWordsLevel') {
                createSetBloomFilterDebounced(this, state, BLOOM_FILTER_N, BLOOM_FILTER_K);
            }
            if (option.key === 'doneIntro') {
                localStorage.setItem('doneIntro', option.value);
            }
            else {
                this.commit('setNeedSync', true);
            }
        },
        setDeepOption(state, option) {
            state.options[option.key][option.key2] = option.value;
            syncOptionsDebounced(state);
        },
        setDict(state, dict) {
            state.DICT = dict;
            createSetBloomFilterDebounced(this, state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setHskWords(state, words) {
            state.HSK_WORDS = words;
            createSetBloomFilterDebounced(this, state, BLOOM_FILTER_N, BLOOM_FILTER_K);
        },
        setShowsDictionary(state, dict) {
            state.SHOWS_DICTIONARY = dict;
        },
        setAnkiAdvancedCards(state, val) {
            state.options.anki.advancedCards = val;
            syncOptionsDebounced(state);
        },
        setAnkiCardsAdvancedToggled(state, val) {
            state.options.anki.advancedToggled = val;
            syncOptionsDebounced(state);
        },
        setAnkiCardsBasicToggled(state, val) {
            state.options.anki.basicToggled = val;
            syncOptionsDebounced(state);
        },
        setAnkiCardsClozeIncludeHint(state, val) {
            state.options.anki.clozeIncludeHint = val;
            syncOptionsDebounced(state);
        },
        setSubmittedExercises(state, val) {
            state.playerData[val.playerId].submittedExercises[val.key] = val.value;
        },
        setPage(state, val) {
            let url = '/' + val;
            if (val === 'player') {
                const showId = state.playerData.player.showId;
                const season = state.playerData.player.season;
                const episode = state.playerData.player.episode;
                url += `/${showId}/${season + 1}/${episode + 1}`;
            }
            window.history.pushState(null, '', url);
            state.page = val;
            this.commit('setCloseAllDialogs'); // close any open dialogs since we're navigating away
        },
        setURL(state, url) {
            state.url = {href: url.href, pathname: url.pathname};
            if (
                url === null ||
                state.STRINGS === null ||
                state.showList === null
                // NOTE: if you add another state condition here, need to call setURL again when it's set
            ) return;

            if (BROWSER_EXTENSION) {
                //
                // Browser Extension Logic
                //

                this.commit('resetPlayerData', 'player');
                this.commit('setCaptionId', {playerId: 'player', value: extractCurrentCaptionId(state.STRINGS, state.localVideoHash, url.href)});
                const showInfo = getShowInfo('player', null, state);
                if (isNone(state.captionData) || isNone(showInfo)) return;
                const [season, episode] = findVideoInShowInfo(showInfo, state.playerData[val.playerId].captionId);

                this.commit('setPlayerData', {
                    playerId: 'player',
                    showId: showInfo.showId,
                    season: season,
                    episode: episode,
                });
            } else {
                //
                // Website Routing Logic
                //
                const parts = url.pathname.split('/').filter((s) => s.length > 0);

                if (parts[0] === 'player') {
                    this.commit('resetPlayerData', 'player');
                    const showId = parts[1];
                    if (parts.length >= 4) {
                        // Pattern: player/show/season/episode/(caption)
                        const seasonIdx = parseInt(parts[2]) - 1;
                        const episodeIdx = parseInt(parts[3]) - 1;
                        let captionIdx = null;
                        if (parts.length === 5) {
                            captionIdx = parseInt(parts[4]) - 1;
                        }
                        this.commit('setPlayerData', {
                            playerId: 'player',
                            showId: showId,
                            season: seasonIdx,
                            episode: episodeIdx,
                            navigateToCaptionIdx: captionIdx,
                        });
                    }
                    else if (parts.length === 2) {
                        // Pattern: player/movie/
                        this.commit('setPlayerData', {
                            playerId: 'player',
                            showId: showId,
                            season: 0,
                            episode: 0,
                        });
                    }
                    else if (parts.length === 3) {
                        // Pattern: player/movie/caption
                        const captionIdx = parseInt(parts[2]) - 1;
                        this.commit('setPlayerData', {
                            playerId: 'player',
                            showId: showId,
                            season: 0,
                            episode: 0,
                            navigateToCaptionIdx: captionIdx,
                        });
                    }

                    const playerData = state.playerData.player; 
                    this.commit('setCaptionId', {playerId: 'player', value: getCaptionIdFromShowData(state.showList, playerData.showId, playerData.season, playerData.episode)});
                }
                else if (state.accountEmail === null && parts[0] === 'account' && parts.length === 2 && ['register', 'login'].includes(parts[1])) {
                    state.showDialog.account = parts[1];
                }

                if (parts.length === 0) this.commit('setPage', 'content'); // default
                else this.commit('setPage', parts[0]);
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

    // Listen for custom event from local video page
    window.addEventListener('lazybugviewlocal', function(event) {
        store.commit('setLocalVideoHash', event.detail);
    });

    // Observe position changes of the url
    new MutationObserver((mutations) => {
        // The URL and video may change without reloading page, e.g. Youtube is an SPA
        if (store.state.url && window.location.href !== store.state.url.href) {
            store.commit('setURL', window.location);
        }
     }).observe(document, {subtree: true, childList: true});
}

const FETCH_PUBLIC_RESOURCES = [
    ['strings.json', 'strings', 'setStringsList', true],
    ['show_list_full.json', 'show list', 'setShowList', true],
    ['simple_chars.json', 'simple chars list', 'setSimpleCharsList', false],
    ['public_cedict.json', 'dictionary', 'setDict', false],
    ['hsk_words.json', 'HSK word list', 'setHskWords', false],
    ['shows_dictionary.json', 'Show word dictionary', 'setShowsDictionary', false],
];


function fetchInitialResources() {
    let numFetched = 0;
    let numRequired = FETCH_PUBLIC_RESOURCES.reduce((acc, r) => acc + (r[3] ? 1 : 0), 0);
    for (const [filename, errorName, mutation, requiredForLoading] of FETCH_PUBLIC_RESOURCES) {
        fetchVersionedResource(filename, function (data) {
            if (requiredForLoading) {
                numFetched++;
            }
            if (data === 'error') {
                store.commit('setResourceFetchError', errorName);
            }
            else {
                if (requiredForLoading) {
                    let $el = document.querySelector('.loading-text');
                    if ($el) {
                        $el.innerText = 'Loading' +'.'.repeat(numFetched);
                    }
                }
                store.commit('resetResourceFetchError', errorName);
                store.commit(mutation, data);
            }
            if (numFetched == numRequired) {
                store.commit('setFetchedAllPublicResources');
            }
        });
    }

    fetchPersonalDataToStore(store, function(success) {
        // Show the intro
        if (! store.state.options.doneIntro) {
            store.commit('setShowDialog', { dialog: 'intro', value: true });
        }
    });
}

store.commit('setURL', document.location); // initial

if (BROWSER_EXTENSION) {
    FETCH_PUBLIC_RESOURCES.unshift(['video_list.json', 'video list', 'setVideoList', true]);
    // We have to wait for the iframe to load before we can fetch stuff from it
    //lazybugIframe.addEventListener('load', fetchInitialResources);
    // NOTE: 'load' event sometimes doesn't trigger, let's just ping the iframe until it responds
    let pingIframeInterval = setInterval(function() {
        sendMessageToBackground({type: 'ping'}, function(response) {
            if (response !== 'pong') return;
            clearInterval(pingIframeInterval);
            fetchInitialResources();

            // Fetch login info
            sendMessageToBackground({type: 'getLoginCredentials'}, function(response) {
                if (response !== null) {
                    store.commit('setLogin', {email: response.email, accessToken: response.accessToken});
                }
            });
        });
    }, 100);
}
else {
    FETCH_PUBLIC_RESOURCES.push(['bloom_filters.json', 'show bloom filters', 'setBloomFilters', false]);
    fetchInitialResources();

    window.onpopstate = (event) => {
        store.commit('setURL', document.location);
    }

    let numCss = Array.from(document.querySelectorAll('head link')).filter(($el) => $el.href.endsWith('css')).length;
    let checkCssInterval = setInterval(function() {
        if (document.styleSheets.length === numCss) {
            clearInterval(checkCssInterval);
            store.commit('setCssLoaded');
            if (document.querySelector('#haslazybugextension')) {
                store.commit('setHasLazybugExtension');
            }
        }
    }, 100);

    let checkExtensionInterval = setInterval(function() {
        if (document.querySelector('#haslazybugextension')) {
            clearInterval(checkExtensionInterval);
            store.commit('setHasLazybugExtension');
        }
    }, 300);
}
