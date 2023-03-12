<template>
    <Caption
        class="lazybug"
        v-if="$store.state.captionId && $store.state.youtubeAPIReady"
        v-bind:captionId="$store.state.captionId"
        v-bind:AVElement="$store.state.AVElement"
        v-bind:videoDuration="$store.state.videoDuration"
        v-bind:videoAPI="$store.state.videoAPI"
    />
</template>

<script>
import Caption from './Caption.vue'

export default {
    components: {
        Caption,
    },
    mounted: function() {
        $q = this.$q; // global variable in shared.js
    }
};
</script>

<style>
</style>
