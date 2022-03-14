const mixin = {
    methods: {
        sm2tr(text) {
            if (this.$store.state.DICT === null) return null;
            if (this.$store.state.options.characterSet == 'sm') return text;

            let trText = '';
            let nextIdx = 0;
            while (nextIdx < text.length) {
                let foundStr = text.substring(nextIdx, nextIdx+1);
                for (var i = nextIdx+1; i < text.length; i++) {
                    const subStr = text.substring(nextIdx, i);
                    if (this.$store.state.DICT[foundStr] !== undefined) {
                        break;
                    }
                    foundStr = subStr;
                }
                let entries = this.$store.state.DICT[foundStr];
                if (entries !== undefined) {
                    trText += dictArrayToDict(entries[0]).hzTrad;
                }
                else {
                    trText += foundStr;
                }

                nextIdx += foundStr.length;
            }

            return trText;
        },
        appendSessionLog(data) {
            appendSessionLog(this.$store.state, data);
        },
        createSession() {
            createSession(this.$store.state);
        },
    },
    computed: {
        lvlKnowledge: function() {
            if (this.$store.state.DICT === null || this.$store.state.HSK_WORDS === null) return {};
            const d = this.$store.state.DICT;
            const knowledge = {};
            for (let lvl = 1; lvl <= 6; lvl++) {
                const knowPy = lvl <= this.$store.state.options.knownLevels.py;
                const knowHz = lvl <= this.$store.state.options.knownLevels.hz;
                const knowTr = lvl <= this.$store.state.options.knownLevels.tr;

                for (const hz of this.$store.state.HSK_WORDS[lvl-1]) {
                    if (knowHz) applyKnowledge(d, knowledge, 'hz', hz, null, null, null, KnowledgeKnown, KnowledgeKnown, false);
                    const entries = d[hz];
                    if (entries === undefined) continue;

                    for (let entry of entries) {
                        entry = dictArrayToDict(entry);
                        const pys = entry.pys;
                        if (knowPy) applyKnowledge(d, knowledge, 'py', hz, pys, null, null, KnowledgeKnown, KnowledgeKnown, false);
                        if (knowTr) applyKnowledge(d, knowledge, 'tr', hz, pys, null, null, KnowledgeKnown, KnowledgeKnown, false);
                    }
                }
            }
            return knowledge;
        },
        videoWordStats: function() {
            if (this.$store.state.captionData === null) return {};
            const wordStats = {};
            for (let line of this.$store.state.captionData.lines) {
                line = captionArrayToDict(line, this.$store.state.captionData);
                for (let alignment of line.alignments) {
                    const hz = alignment[2];
                    const py = alignment[3].map((item) => item[0]).join('');
                    const key = `${hz}-${py}`;
                    if (wordStats[key] === undefined) {
                        wordStats[key] = 0;
                    }
                    wordStats[key] += 1;
                }
            }

            return wordStats;
        },
        purePeekStates: function() {
            const states = this.$store.state.peekStates;
            states['translation'] = states['translation'] && !this.showStates['translation'];
            for (var i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = states[type][i] && !this.showStates[type][i];
                }
            }
            return states;
        },
    },
};

