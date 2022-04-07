<template>
    <div class="q-pa-md">
        <q-table
            style="display: inline-block"
            ref="tableRef"
            title="Starred"
            :rows="rows"
            :columns="columns"
            :selected-rows-label="getSelectedString"
            selection="multiple"
            v-model:selected="selected"
            :pagination="pagination"
        >
          <template v-slot:body="props">
              <q-tr v-if="props.row.isNewSession">
                  <q-td colspan="100%">
                      <div style="font-size: 1.2em" ><b>{{ timestampToYYYMMDD(props.row.time) }}</b>: {{ props.row.video }}</div>
                  </q-td>
              </q-tr>
              <q-tr :props="props">
                  <q-td>
                      <q-checkbox v-model="props.selected" color="primary" />
                  </q-td>
                  <q-td
                     v-for="col in props.cols"
                     :key="col.name"
                     :props="props"
                     @click="props.expand = !props.expand"
                     :style="{ cursor: 'pointer' }"
                     v-html="col.value"
                     >
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
            {name: 'hz', field: 'hz', label: 'Hanzi'},
            {name: 'py', field: 'py', label: 'Pinyin'},
            {name: 'tr', field: 'tr', label: 'Translation'},
            {name: 'translation', field: 'translation', label: 'Sentence Translation'},
        ],
        selected: [],
        pagination: {
            rowsPerPage: 50
        },
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
        timestampToYYYMMDD: function(val) {
            return (new Date(val)).toISOString().split('T')[0];
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

            let lastSessionId = null;
            for (let i = 0; i < this.starEvents.length; i++) {
                const [type, eventData, sessionTime, captionId] = this.starEvents[i];
                const [_, idx, data] = eventData;
                const wordData = getWordData(data.data, data.translationIdx);
                const t0 = data.t0;
                const t1 = data.t1;
                const dt = data.dt;

                const sessionId = `${sessionTime}-${captionId}`;

                const alignmentIdx = wordData.alignmentIndices[idx];
                const alignment = data.data.alignments[alignmentIdx];
                const [startIdx, endIdx, ...rest] = alignment;

                const text = data.data.texts.join(' ');
                const fullHz = `${text.substring(0, startIdx)}<b>${text.substring(startIdx, endIdx)}</b>${text.substring(endIdx)}`;

                const py = idx !== null ? wordData.py[idx] : '';
                const hz = idx !== null ? wordData.hz[idx] : '';
                const tr = idx !== null ? wordData.tr[idx] : '';

                const id = `${sessionTime}-${dt}-${captionId}-${py}-${hz}-${tr}-${wordData.translation}`;
                console.log(id);
                rows.push({
                    id: id,
                    idx: i,
                    type: type,
                    py: py,
                    hz: fullHz,
                    tr: tr,
                    translation: wordData.translation,
                    time: sessionTime,
                    video: captionId,
                    isNewSession: sessionId !== lastSessionId,
                });
                lastSessionId = sessionId;
            }

            return rows.reverse();
        },
    },
};
</script>

<style>
</style>
