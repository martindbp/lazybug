<template>
    <div @mouseover="mouseOver" @mouseout="mouseOut" class="zimucaptiondiv">
        <CaptionMenu
            ref="menu"
            :class="{ show: showMenu }"
            v-bind="$props"
            v-on:seeked="$emit('seeked')"
        />
        <CaptionContent
            v-bind:data="currCaption"
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
    }},
    methods: {
        mouseOver: function() {
            this.showMenu = true;
        },
        mouseOut: function() {
            this.showMenu = false;
        },
    },
};

</script>
