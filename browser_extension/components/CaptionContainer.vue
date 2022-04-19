<template>
    <div @mouseover="mouseOver" @mouseout="mouseOut" :class="{zimucaptiondiv: true, moving: $store.state.isMovingCaption, paused: paused}">
        <CaptionMenu
            ref="menu"
            :class="{ show: showMenu }"
            v-bind="$props"
            v-bind:data="showData"
            v-on:seeked="$emit('seeked')"
        />
        <div class="loadingcontent" v-if="$store.state.resourceFetchError !== null">
            Error fetching {{ $store.state.resourceFetchError }}, try reloading page
        </div>
        <div class="loadingcontent" v-else-if="isLoading">
            Loading resources...
        </div>
        <div class="initialcontent" v-else-if="showData === null && firstCaption && currTime >= 0 && currTime < firstCaption.t0">
            Video has <i>{{ translationType }}</i> sentence translations
            <br />
            <br />
            <q-btn color="primary" label="Go to first subtitle" @click="clickFirst"/>
        </div>
        <div class="initialcontent" v-else-if="showData === null">
            Video has <i>{{ translationType }}</i> sentence translations
            <br />
            <br />
            <q-btn color="primary" label="Go to next subtitle" @click="clickNext"/>
        </div>
        <CaptionContent
            :class="{ showpeekall: showMenu }"
            v-else
            v-bind:data="showData"
            v-bind:fadeOut="fadeOut"
            v-bind:currTime="currTime"
            v-bind:currentCaptionIdx="currentCaptionIdx"
        />
    </div>
</template>

<script>
import CaptionMenu from './CaptionMenu.vue'
import CaptionContent from './CaptionContent.vue'

export default {
    props: [
        'currentCaptionIdx',
        'firstCaption',
        'prevCaption',
        'currCaption',
        'nextCaption',
        'currTime',
        'paused',
        'AVElement',
        'isLoading',
        'translationType',
    ],
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
        clickFirst: function() {
            this.AVElement.currentTime = this.firstCaption.t0 + 1e-3;
            this.AVElement.play();
            this.$emit('seeked');
        },
        clickNext: function() {
            this.AVElement.currentTime = this.nextCaption.t0 + 1e-3;
            this.AVElement.play();
            this.$emit('seeked');
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
.initialcontent {
    text-align: center;
    padding-top: 25px;
    padding-bottom: 25px;
    padding-left: 50px;
    padding-right: 50px;
}

.loadingcontent {
    text-align: center;
    padding-top: 50px;
    padding-bottom: 50px;
    padding-left: 100px;
    padding-right: 100px;
}

.zimucaptiondiv {
    color: white;
    background-color: rgba(0, 0, 0, 0.75);
    text-align: left;
    font-size: 18px;
    padding: 0px;
    min-width: 7em;
    filter: drop-shadow(rgb(25, 25, 25) 3px 3px 5px);
}

.zimucaptiondiv.paused,
.paused .captionmenu{
    background-color: rgba(0, 0, 0, 1.0);
    transition: background-color 300ms linear;
}

</style>
