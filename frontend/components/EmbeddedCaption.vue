<template>
    <Caption
        class="lazybug"
        v-if="captionId && $store.state.youtubeAPIReady"
        v-bind:playerId="playerId"
        v-bind:captionId="captionId"
        v-bind:AVElement="AVElement"
        v-bind:videoDuration="videoDuration"
        v-bind:videoAPI="videoAPI"
    />
</template>

<script>
import Caption from './Caption.vue'

export default {
    mixins: [mixin],
    props: ['playerId'],
    components: {
        Caption,
    },
    mounted: function() {
        $q = this.$q; // global variable in shared.js
    },
};
</script>

<style>
</style>
