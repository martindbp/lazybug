<template>
    <div ref="historypage">
        <q-table
          :rows="rows"
          :columns="columns"
          :pagination="pagination"
          :loading="isLoading"
          row-key="name"
          :class="{historytable: true, mobile: isMobile}"
        >
            <template v-slot:body="props">
                <q-tr :props="props" @click="clickVideo(props)" style="cursor: pointer;">
                    <q-td key="video" :props="props" >
                        <img width="100" :src="thumbnailURL(props.cols[0].value)" />
                    </q-td>
                    <q-td key="name" :props="props">
                        {{ props.cols[1].value }}
                    </q-td>
                </q-tr>
            </template>
        </q-table>
    </div>
</template>

<script>

export default {
    mixins: [mixin],
    data: function() { return {
        isLoading: true,
        rows: [],
        pagination: {
            rowsPerPage: 25,
        },
        columns: [
            {
                name: 'video',
                field: 'captionId',
                required: true,
                label: 'Video',
                align: 'left',
            },
            {
                name: 'name',
                field: 'name',
                required: true,
                label: 'Name',
                align: 'left',
                sortable: true
            },
        ],
    }},
    updated: function() {
        if (this.$refs.historypage && this.$refs.historypage.style.display !== 'none') {
            // We navigated to this page, so update
            this.updateHistory();
        }
    },
    computed: {
        showList: function() {
            return this.$store.state.showList;
        },
    },
    watch: {
        showList: {
            immediate: true,
            handler: function(newData) {
                if (! newData) return;
                this.updateHistory();
            },
        },
    },
    methods: {
        updateHistory: function() {
            if (this.showList === null) return;

            const self = this;
            getViewingHistory(0, null, function(data) {
                data = data.filter((row) => row.seasonIdx !== null);  // bogus data that was probably added because of a bug
                for (const row of data) {
                    const showId = row.showId;
                    row.showInfo = self.showList[showId];
                    const showName = resolveShowName(row.showInfo.name);
                    const seasonName = getSeasonName(row.showInfo, row.seasonIdx);
                    const episodeName = getEpisodeName(row.showInfo, row.seasonIdx, row.episodeIdx);
                    row.name = `${showName} - ${seasonName} ${episodeName}`;
                }
                self.rows = data;
                self.isLoading = false;
            });
        },
        thumbnailURL: function(captionId) {
            return youtubeThumbnailURL(captionId);
        },
        clickVideo: function(props) {
            this.setPlaying(props.row.showId, props.row.seasonIdx, props.row.episodeIdx);
        },
    }
};
</script>
<style>
.historytable {
    display: inline-block;
    margin-top: 50px;
    margin-left: 50px;
}

.historytable.mobile {
    margin: 0;
}
</style>
