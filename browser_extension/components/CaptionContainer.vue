<template>
    <div @mouseover="mouseOver" @mouseout="mouseOut" class="zimucaptiondiv">
        <CaptionLeftMenu
            ref="leftmenu"
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
import CaptionLeftMenu from './CaptionLeftMenu.vue'
import CaptionContent from './CaptionContent.vue'

export default {
    props: ['prevCaption', 'currCaption', 'nextCaption', 'currTime', 'paused', 'AVElement'],
    components: {CaptionContent, CaptionLeftMenu},
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
