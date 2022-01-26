<template>
    <q-dialog v-model="show" dark>
        <q-card style="width: 600px" class="q-px-sm q-pb-md">
            <q-card-section>
                <div class="text-h4">Dictionary</div>
            </q-card-section>
            <q-card-section align="center">
                <div class="text-h4">
                    <span
                        :class="{char: true, highlight: i >= highlightRange[0] && i < highlightRange[1], firstchar: i == highlightRange[0], lastchar: i == highlightRange[1] - 1}"
                        v-for="(char, i) in text"
                        @mouseover="mouseoverChar = i"
                        @click="clickChar(i)"
                    >
                        {{ char }}
                    </span>
                </div>
            </q-card-section>
            <q-card-section align="left" style="padding: 25px; max-height: 500px; height: 500px" class="scroll">
                <q-separator color="orange" v-if="showEntries.length > 0"/>
                <div v-for="entry in showEntries">
                    <div class="text-h4" :style="{ color: 'lightgray' }">{{ entry.hz }}</div>
                    <div class="text-h6" v-for="item in entry.items">
                        <span v-for="(py, i) in item[1]" :style="{ color: COLORS[parseInt(item[0][i].slice(-1))] }">
                            {{ py }}
                        </span>: {{ item[2].join(' ‧ ') }}</div>
                    <q-separator color="orange" />
                </div>
                <div class="text-h5" v-if="showEntries.length === 0 && text !== ''">
                    Click on a word to see the dictionary pinyin and translations
                </div>
            </q-card-section>
            <q-card-actions align="right" class="text-teal">
                <q-btn flat label="OK" @click="clickClose"></q-btn>
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>


export default {
    props: ['caption'],
    components: { },
    data: function() { return {
        mouseoverChar: null,
        showEntries: [],
        COLORS: [
            null,
            '#DC143C', // red
            'orange',
            '#228B22', // green
            '#4169E1', // blue
            'gray'],
    }},
    computed: {
        text: function() {
            if (this.caption.dummy) return '';
            return this.caption.texts.join(' ');
        },
        show: {
            get: function() { return this.$store.state.showDictionary; },
            set: function(val) { this.$store.commit('setShowDictionary', val); },
        },
        dictEntries: function() {
            if (this.highlightRange[0] < 0) return [];

            const entries = []
            for (var i = this.highlightRange[0]+1; i <= this.highlightRange[1]; i++) {
                const text = this.text.substring(this.highlightRange[0], i)
                if (DICT[text] !== undefined) {
                    entries.push({hz: text, items: DICT[text]});
                }
            }

            return entries.reverse();
        },
        highlightRange: function() {
            if (this.mouseoverChar === null) return [-1, -1];

            let range = [-1, -1];
            for (var i = this.mouseoverChar+1; i < this.text.length+1; i++) {
                if (DICT[this.text.substring(this.mouseoverChar, i)] !== undefined) {
                    range = [this.mouseoverChar, i];
                }
            }
            return range;
        },
    },
    watch: {
        caption: function(newVal, oldVal) {
            this.showEntries = [];
            this.mouseoverChar = null;
        },
    },
    methods: {
        clickClose: function(event) {
            // Remove the "zimuquasardialog" class from the dialog parent, otherwise there's some flickering
            document.querySelector('.zimuquasardialog').classList.remove('zimuquasardialog');
            this.show = false;
        },
        clickChar: function(event) {
            this.showEntries = this.dictEntries;
        },
    },
}
</script>
<style>

.zimuquasardialog {
    z-index: 9999;
    position: absolute;
    left: 0;
}

.char {
    cursor: pointer;
}

.char.highlight {
    background: gray;
}

.firstchar {
    border-radius: 5px 0px 0px 5px;
}

.lastchar {
    border-radius: 0px 5px 5px 0px;
}

.firstchar.lastchar {
    border-radius: 5px;
}

</style>
