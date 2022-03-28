<template>
    <div class="q-pa-md">
        <q-table
            style="display: inline-block"
            ref="tableRef"
            title="Starred"
            :rows="rows"
            :columns="columns"
            row-key="content"
            :selected-rows-label="getSelectedString"
            selection="multiple"
            v-model:selected="selected"
        />
        <div class="q-mt-md">
            <q-btn label="Export to Anki" @click="exportToAnki"/>
        </div>
    </div>
</template>

<script>

export default {
    props: {
    },
    data: function() { return {
        log: null,
        columns: [
            {name: 'time', field: 'time', label: 'Date', format: val => (new Date(val)).toISOString().split('T')[0],},
            {name: 'video', field: 'video', label: 'Video'},
            {name: 'content', field: 'content', label: 'Content'}
        ],
        selected: [],
    }},
    mounted: function() {
        const self = this;
        getLog(function(data) {
            self.log = data;
        });
    },
    methods: {
        reverseEventsMap: function(eventId) {
            return reverseEventsMap[eventId];
        },
        getSelectedString: function() {
            return this.selected.length === 0 ? '' : `${this.selected.length} item${this.selected.length > 1 ? 's' : ''} selected of ${this.rows.length}`
        },
        exportToAnki: function() {
                //const cloze = captionToAnkiCloze(this.wordData, this.hiddenStates, type, i, this.$store.state.videoId, this.data.t0, this.data.t1);
                //console.log(cloze);
                //updateClipboard(cloze, this.$q, 'Anki cloze card copied to clipboard');
        },
    },
    watch: {
    },
    computed: {
        rows: function() {
            const rows = [];
            if (this.log === null) return rows;

            for (const session of this.log) {
                for (const event of session.events) {
                    const eventName = reverseEventsMap[event[0]];
                    if (eventName.startsWith("EVENT_STAR")) {
                        let type = null;
                        if (eventName.endsWith('PY')) {
                            type = 'py';
                        }
                        else if (eventName.endsWith('HZ')) {
                            type = 'hz';
                        }
                        else if (eventName.endsWith('TR')) {
                            type = 'tr';
                        }
                        else if (eventName.endsWith('TRANSLATION')) {
                            type = 'translation';
                        }
                        const idx = event[1];
                        const wordData = event[2].words;
                        let content = null;
                        if (type === 'translation') {
                            content = wordData.translation;
                        }
                        else {
                            const other = [];
                            const main = wordData[type][idx];
                            for (const t of ['py', 'hz', 'tr']) {
                                if (t !== type) {
                                    other.push(wordData[t][idx]);
                                }
                            }
                            content = `${main} (${other.join('/')})`;
                        }
                        rows.push({time: session.sessionTime, video: session.captionId, content: content});
                    }
                }
            }

            return rows;
        },
    },
};
</script>

<style>
</style>
