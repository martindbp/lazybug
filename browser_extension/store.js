const KnowledgeUnknown = 0;
const KnowledgeKnown = 1;
const KnowledgeLearning = 2;

const store = new Vuex.Store({
    state: {
        knowledge: Vue.ref({}),
        captionFontScale: 0.5,
        captionOffset: [0, 0],
        peekStates: Vue.ref({'py': [], 'hz': [], 'tr': [], 'translation': false}),
        showOptions: false,
        showDictionary: false,
        options: Vue.ref({
            pauseAfterCaption: true,
            knownLevels: {
                py: 4,
                hz: 2,
                tr: 4,
            },
        }),
    },
    mutations: {
        setShowOptions(state, val) {
            state.showOptions = val;
        },
        setShowDictionary(state, val) {
            state.showDictionary = val;
        },
        setKnowledgeKey(state, keyVal) {
            state.knowledge[keyVal.key] = keyVal.val;
        },
        setKnowledgeKeys(state, keysVals) {
            for (let i = 0; i < keysVals.keys.length; i++) {
                const keyVal = {key: keysVals.keys[i], val: keysVals.vals[i]};
                state.knowledge[keyVal.key] = keyVal.val;
            }
        },
        increaseCaptionFontScale(state) {
            state.captionFontScale = Math.min(state.captionFontScale + 0.1, 1.0);
        },
        decreaseCaptionFontScale(state) {
            state.captionFontScale = Math.max(state.captionFontScale - 0.1, 0.0);
        },
        setCaptionOffset(state, offset) {
            state.captionOffset = offset;
        },
        setPeekState(state, val) {
            if (val.i === undefined || val.i === null) {
                state.peekStates[val.type] = true;
            }
            else {
                state.peekStates[val.type][val.i] = true;
            }
        },
        setPeekStates(state, val) {
            state.peekStates = val;
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
        },
        setKnownLevel(state, val) {
            state.options.knownLevels[val.type] = val.level;
        },
    },
    getters: {
        getKnowledgeState: (state) => (key) => {
            const knowledgeState = state.knowledge[key];
            if (knowledgeState  === undefined) return undefined;
            return knowledgeState;
        }
    }
})

