<template>
    <div>
    <q-tabs
        v-model="contentTab"
        no-caps
        outside-arrows
        mobile-arrows
        class="bg-white text-dark"
    >
        <q-tab name="shows" label="Shows" />
        <q-tab name="movies" label="Movies" />
        <q-tab name="other" label="Other" />

    </q-tabs>
    <q-tab-panels class="contentpanels" v-model="contentTab">
        <q-tab-panel name="shows">
            <ShowTable type="tv" />
        </q-tab-panel>
        <q-tab-panel name="movies">
            <ShowTable type="movie" />
        </q-tab-panel>
        <q-tab-panel name="other">
            <ShowTable type="other" />
        </q-tab-panel>
    </q-tab-panels>
    </div>
</template>

<script>
import ShowTable from './ShowTable.vue'

export default {
    mixins: [mixin],
    components: {
        ShowTable,
    },
    data: function() { return {
        contentTab: 'shows',
    }},
};
</script>

<style>
.contentpanels .q-panel {
    overflow: visible !important;
}

.contentpanels .q-panel,
.contentpanels .q-panel div {
    height: auto !important;
}
</style>
