<template>
    <q-table
      :rows="rows"
      :columns="columns"
      :pagination="pagination"
      :loading="isLoading"
      row-key="name"
      style="display: inline-block; margin-top: 50px;"
    >
        <template v-slot:header-cell="props">
            <q-th :props="props">
                {{ props.col.label }}
                <span v-if="columnFilters[props.col.name] !== undefined">
                    <q-badge class="clickablebadge" @click.stop.prevent="removeFilter(...filter)" v-for="filter in columnFilters[props.col.name]" :color="mapToColor(filter[1], filter[2])">{{filter[2]}}</q-badge>
                </span>
            </q-th>
        </template>
        <template v-slot:body="props">
            <q-tr :props="props" @click="props.expand = !props.expand" :style="{ cursor: 'pointer' }" >
                <q-td key="name" :props="props" class="text-subtitle1" style="max-width: 350px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                    {{ props.cols[0].value }}
                </q-td>
                <q-td key="difficulty" :props="props">
                    <q-badge :color="mapDifficultyToColor(props.cols[1].value)">
                        {{ props.cols[1].value }}
                    </q-badge>
                </q-td>
                <q-td key="douban" :props="props">
                    <span v-if="props.cols[2].value === 'N/A'">N/A</span>
                    <q-badge v-else :color="mapDoubanToColor(props.cols[2].value)">
                        {{ props.cols[2].value }}
                    </q-badge>
                </q-td>
                <q-td key="type" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('type', 'type', props.cols[3].value)" :color="mapToColor('type', props.cols[3].value)">
                        {{ props.cols[3].value }}
                    </q-badge>
                </q-td>
                <q-td key="year" :props="props" style="white-space: normal; max-width: 200px;">
                    {{ props.cols[4].value }}
                </q-td>
                <q-td key="genres" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('genres', 'genres', genre)" v-for="genre in props.cols[5].value" :color="mapToColor('genres', genre)">
                        {{ genre }}
                    </q-badge>
                </q-td>
                <q-td key="synopsis" :props="props" style="white-space: normal; max-width: 200px;">
                    {{ props.cols[6].value }}
                </q-td>
                <q-td key="sources" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('sources', 'caption_source', props.cols[7].value[0])" :color="mapToColor('caption_source', props.cols[7].value[0])">
                        {{ props.cols[7].value[0] }}
                    </q-badge>
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('sources', 'translation_source', props.cols[7].value[1])" :color="mapToColor('translation_source', props.cols[7].value[1])">
                        {{ props.cols[7].value[1] }}
                    </q-badge>
                </q-td>
                <q-td key="num_processed" :props="props" style="white-space: normal; max-width: 200px;">
                    {{ props.cols[8].value }}
                </q-td>
                <q-td key="free" :props="props" style="white-space: normal; max-width: 200px;">
                    <q-badge class="clickablebadge" @click.stop.prevent="addFilter('free', 'free', props.cols[9].value)"  :color="mapToColor('free', props.cols[9].value)">
                        {{ props.cols[9].value ? 'free' : 'paid' }}
                    </q-badge>
                </q-td>
            </q-tr>
            <q-tr v-if="props.expand" v-show="props.expand" :props="props">
                <q-td colspan="100%">
                    <div style="display: inline-block; vertical-align: top" v-html="rowYoutubeEmbedCode(props.row)" />
                    <div style="display: inline-block; vertical-align: top; max-width: 800px; white-space: normal; word-break: break-all; margin: 30px;">
                        <div v-if="props.row.type === 'movie'"><a :href="youtubeURL(props.row, 0, 0)">Go</a></div>
                        <div
                            v-else
                            v-for="(season, i) in props.row.seasons"
                        >
                            <span>{{ props.row.seasons.length === 1 ? 'Episodes' : season.name || `Season ${i+1}` }}:</span>
                            <br>
                            <span style="margin-left: 3px;" v-for="(episode, j) in season.episodes"><a :href="youtubeURL(props.row, i, j)" > {{ j + 1 }} </a></span>
                        </div>
                    </div>
                </q-td>
            </q-tr>
        </template>
    </q-table>
</template>

<script>
var roundToScale = function(n, scale) {
    return parseFloat((Math.round(n / scale) * scale).toFixed(1));
};

export default {
    data: function() { return {
        pagination: {
            rowsPerPage: 25,
        },
        columns: [
          {
            name: 'name',
            required: true,
            label: 'Name',
            align: 'left',
            field: row => row.name.en ? `${row.name.hz} | ${row.name.en}` : row.name,
            sortable: true
          },
          {
            name: 'difficulty',
            required: true,
            label: 'Difficulty',
            align: 'left',
            field: row => roundToScale(10*(row.difficulty !== undefined ? row.difficulty : row.difficulty_manual), 0.1),
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'douban',
            required: true,
            label: 'Douban score',
            align: 'left',
            field: row => row.douban || 'N/A',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'type',
            required: true,
            label: 'Type',
            align: 'left',
            field: row => row.type || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'year',
            required: true,
            label: 'Year',
            align: 'left',
            field: row => row.year || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'genres',
            required: true,
            label: 'Genres',
            align: 'left',
            field: row => row.genres,
            sortable: true
          },
          {
            name: 'synopsis',
            required: true,
            label: 'Synopsis',
            align: 'left',
            field: row => row.synopsis || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'sources',
            required: true,
            label: 'Sources',
            align: 'left',
            field: row => [row.caption_source, row.translation_source],
            sortable: true
          },
          {
            name: 'num_processed',
            required: true,
            label: 'Episodes/Videos',
            align: 'left',
            field: row => row.num_processed || '-',
            format: val => `${val}`,
            sortable: true
          },
          {
            name: 'free',
            required: true,
            label: 'Free',
            align: 'left',
            field: row => row.free,
            sortable: true
          },
        ],
        filters: null,
    }},
    computed: {
        rows: function() {
            if (this.$store.state.showList === null) return [];
            let rows = Object.values(this.$store.state.showList).filter((show) => show.released);
            let filters = this.filters;
            if (filters !== null) {
                rows = rows.filter(row => {
                    let allMatch = true;
                    for (const [filterCol, filterProp, filterVal] of filters) {
                        if (Array.isArray(row[filterProp])) {
                            if (! row[filterProp].includes(filterVal)) allMatch = false;
                        }
                        else {
                            if (row[filterProp] !== filterVal) allMatch = false;
                        }
                    }
                    return allMatch;
                });
            }
            return rows;
        },
        columnFilters: function() {
            let colFilters = {};
            if (this.filters === null) return colFilters;

            for (const [col, rowProp, val] of this.filters) {
                colFilters[col] = colFilters[col] || [];
                colFilters[col].push([col, rowProp, val]);
            }
            return colFilters;
        },
        isLoading: function() {
            return this.$store.state.showList === null;
        },
    },
    methods: {
        rowYoutubeEmbedCode: function(row) {
            const captionId = row.seasons[0].episodes[0].id;
            const parts = captionId.split('-');
            const id = parts.slice(1).join('-');
            return getYoutubeEmbedCode(id);
        },
        youtubeURL: function(row, seasonIdx=null, episodeIdx=null) {
            seasonIdx = seasonIdx || 0;
            episodeIdx = episodeIdx || 0;
            const playlist = row.seasons[seasonIdx].youtube_playlist;
            const captionId = row.seasons[seasonIdx].episodes[episodeIdx].id;
            const parts = captionId.split('-');
            const id = parts.slice(1).join('-');

            if ([null, undefined].includes(playlist)) {
                return `https://youtube.com/watch?v=${id}`;
            }
            else {
                return `https://youtube.com/watch?v=${id}&list=${playlist}`;
            }
        },
        mapDifficultyToColor: function(difficulty) {
            if (difficulty < 4) return 'green';
            else if (difficulty < 7) return 'orange';
            else return 'red';
        },
        mapDoubanToColor: function(score) {
            if (score < 7) return 'red';
            else if (score < 8.0) return 'orange';
            else return 'green';
        },
        mapToColor: function(type, val) {
            if (type === 'genres') {
                const colors = ['green', 'blue', 'red', 'orange', 'purple', 'cyan', 'teal', 'light-green', 'amber', 'brown', 'blue-gray', 'indigo'];
                let charCodeSum = 0;
                for (let i = 0; i < val.length; i++) {
                    charCodeSum += val.charCodeAt(i);
                }

                return colors[charCodeSum % colors.length];
            }
            else if (type === 'caption_source') {
                return 'blue';
            }
            else if (type === 'translation_source') {
                return 'green';
            }
            else if (type === 'type') {
                if (val === 'tv') return 'blue';
                else if (val === 'movie') return 'red';
                else return 'green';
            }
            else if (type === 'free') {
                return val ? 'green' : 'red';
            }
        },
        addFilter: function(column, rowProp, value) {
            this.removeFilter(column, rowProp, value);
            if (this.filters === null) {
                this.filters = [];
            }
            this.filters.push([column, rowProp, value]);
        },
        removeFilter: function(column, rowProp, value) {
            if (this.filters === null) return;
            this.filters = this.filters.filter(filter => {
                if (filter[0] === column && filter[1] === rowProp && filter[2] === value) return false;
                return true;
            });
            if (this.filters.length === 0) this.filters = null;
        },
        clearFilters: function() {
            this.filters = null;
        }
    }
};
</script>

<style>
.clickablebadge {
    margin-left: 2px;
    margin-bottom: 2px;
    cursor: pointer;
}
</style>
