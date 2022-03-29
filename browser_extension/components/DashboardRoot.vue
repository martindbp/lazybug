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
        >
          <template v-slot:body="props">
              <q-tr :props="props">
                  <q-td>
                      <q-checkbox v-model="props.selected" color="primary" />
                  </q-td>
                  <q-td
                     v-for="col in props.cols"
                     :key="col.name"
                     :props="props"
                     @click="props.expand = !props.expand"
                     style="cursor: pointer"
                     >
                       {{ col.value }}
                  </q-td>
              </q-tr>
              <q-tr v-show="props.expand" :props="props">
                  <q-td colspan="100%">
                      <div v-html="rowYoutubeEmbedCode(props.row.idx)" />
                  </q-td>
              </q-tr>
          </template>
        </q-table>
        <div class="q-mt-md" v-if="selected.length > 0">
            <q-btn label="Export to Anki" @click="exportToAnki"/>
        </div>
    </div>
</template>

<script>

export default {
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
            let csv = '';
            for (const item of this.selected) {
                const [type, eventData, sessionTime, captionId] = this.starEvents[item.idx];
                const [_, idx, data] = eventData;
                const t0 = data.t0;
                const t1 = data.t1;

                const cloze = captionToAnkiCloze(data.words, data.hidden, type, idx, captionId, t0, t1, true);
                csv += cloze + '\n'
            }
            const filename = 'anki-export-'+(new Date(Date.now())).toISOString().split('T')[0]+'.csv'
            download(filename, csv);
        },
        rowYoutubeEmbedCode: function(rowIdx) {
            const [type, eventData, sessionTime, captionId] = this.starEvents[rowIdx];
            const [_, idx, data] = eventData;
            const t0 = data.t0;
            const t1 = data.t1;
            const [site, id] = captionId.split('-');
            return getYoutubeEmbedCode(id, t0, t1);
        },
    },
    computed: {
        starEvents: function() {
            const events = [];
            if (this.log === null) return events;

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
                        events.push([type, event, session.sessionTime, session.captionId]);
                    }
                }
            }

            return events;
        },
        rows: function() {
            const rows = [];
            if (this.log === null) return rows;

            for (let i = 0; i < this.starEvents.length; i++) {
                const [type, eventData, sessionTime, captionId] = this.starEvents[i];
                const [_, idx, data] = eventData;
                const wordData = data.words;
                const t0 = data.t0;
                const t1 = data.t1;
                const dt = data.dt;

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
                rows.push({id: `${sessionTime}-${dt}-${captionId}-${content}`, idx: i, time: sessionTime, video: captionId, content: content});
            }

            return rows;
        },
    },
};
</script>

<style>
</style>
