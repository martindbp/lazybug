<template>
    <div @mouseover="mouseOver" @mouseout="mouseOut" :class="{zimucaptiondiv: true, moving: $store.state.isMovingCaption}">
        <CaptionMenu
            ref="menu"
            :class="{ show: showMenu }"
            v-bind="$props"
            v-bind:data="showData"
            v-on:seeked="$emit('seeked')"
        />
        <CaptionContent
            :class="{ showpeekall: showMenu }"
            v-if="showData !== null"
            v-bind:data="showData"
            v-bind:fadeOut="fadeOut"
            v-bind:currTime="currTime"
        />
    </div>
</template>

<script>
import CaptionMenu from './CaptionMenu.vue'
import CaptionContent from './CaptionContent.vue'

export default {
    props: ['prevCaption', 'currCaption', 'nextCaption', 'currTime', 'paused', 'AVElement'],
    components: {CaptionContent, CaptionMenu},
    data: function() { return {
        showMenu: false,
        showData: null,
        fadeOut: false,
    }},
    methods: {
        mouseOver: function() {
            this.showMenu = true;
        },
        mouseOut: function() {
            this.showMenu = false;
        },
        updateFadeout: function() {
            // NOTE: we set fadeOut based on currTime in a watch instead of computed, because a computed makes the component re-render every frame
            this.fadeOut = this.showData !== null && (this.currTime > this.showData.t1 + CAPTION_FADEOUT_TIME || this.currTime < this.showData.t0); // eslint-disable-line
        },
    },
    watch: {
        currCaption: {
            immediate: true,
            handler: function(newData, oldData) {
                if (newData !== null && newData !== undefined) this.showData = newData;
                if (newData !== oldData) {
                    this.updateFadeout();
                }
            }
        },
        currTime: {
            immediate: true,
            handler: function(newData, oldData) {
                this.updateFadeout();
            }
        }
    },
};
</script>

<style>
/*
.zimucaptiondiv.moving {
    outline: 2px white solid;
}
.zimucaptiondiv.moving .captionmenu {
    outline: 2px white solid;
}
*/
</style>
