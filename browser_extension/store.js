function getSetKnowledgeValue(state, keyVal) {
    const delta = keyVal.val ? 1 : -1;
    let oldValue = state.knowledge[keyVal.key];
    if (oldValue === undefined) oldValue = 0;
    return oldValue + delta;
}

const store = new Vuex.Store({
    state: {
        knowledge: Vue.ref({}),
        captionFontScale: 0.5,
        captionOffset: [0, 0],
        isPeeking: false,
        showOptions: false,
        options: Vue.ref({
            pauseAfterCaption: true,
            hanziKnowLevel: 2,
            pinyinKnowLevel: 4,
            translationKnowLevel: 4,
        }),
    },
    mutations: {
        setShowOptions(state, val) {
            state.showOptions = val;
        },
        setKnowledgeKey(state, keyVal) {
            state.knowledge[keyVal.key] = getSetKnowledgeValue(state, keyVal);
        },
        setKnowledgeKeys(state, keysVals) {
            for (let i = 0; i < keysVals.keys.length; i++) {
                const keyVal = {key: keysVals.keys[i], val: keysVals.vals[i]};
                state.knowledge[keyVal.key] = getSetKnowledgeValue(state, keyVal);
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
        setPeeking(state, peeking) {
            state.isPeeking = peeking;
        },
        setOption(state, option) {
            state.options[option.key] = option.value;
        },
    },
    getters: {
        getKnowledgeState: (state) => (key) => {
            const k = state.knowledge[key];
            if (k === undefined) return k;
            else return k > 0;
        }
    }
})

