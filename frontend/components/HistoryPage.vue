<template>
    <q-table
      :rows="rows"
      :columns="columns"
      :pagination="pagination"
      :loading="isLoading"
      row-key="name"
      style="display: inline-block; margin-top: 50px; margin-left: 50px"
    >
        <template v-slot:body="props">
            <q-tr :props="props" >
                <q-td key="video" :props="props" >
                    <img width="100" :src="thumbnailURL(props.cols[0].value)" />
                </q-td>
                <q-td key="name" :props="props">
                    {{ props.cols[1].value }}
                </q-td>
            </q-tr>
        </template>
    </q-table>
</template>

<script>

export default {
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
    mounted: function() {
        const self = this;
        getViewingHistory(0, null, function(data) {
            for (const row of data) {
                const showId = row.showId;
                const showInfo = self.$store.state.showList[showId];
                const showName = resolveShowName(showInfo.name);
                const seasonName = getSeasonName(showInfo, row.seasonIdx);
                const episodeName = getEpisodeName(showInfo, row.seasonIdx, row.episodeIdx);
                row.name = `${showName} - ${seasonName} ${episodeName}`;
            }
            self.rows = data;
            self.isLoading = false;
        });
    },
    methods: {
        thumbnailURL: function(captionId) {
            return youtubeThumbnailURL(captionId);
        },
    }
};
</script>

<style>
</style>
