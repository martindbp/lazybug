<template>
    <div @mouseover="mouseOver" @mouseout="mouseOut" :class="{lazybugcaptiondiv: true, moving: $store.state.isMovingCaption, paused: paused, docked: $store.state.captionDocked, mobile: isMobile}">
        <CaptionMenu
            ref="menu"
            :class="{ show: showMenu }"
            v-bind="$props"
            v-bind:data="showData"
            v-on:seeked="$emit('seeked')"
        />
        <div class="loadingcontent" v-if="$store.state.resourceFetchErrors.length > 0">
            Error fetching {{ $store.state.resourceFetchErrors.join(', ') }}, try reloading page
        </div>
        <div class="loadingcontent" v-else-if="isLoading">
            Loading resources...
        </div>
        <div class="initialcontent" v-else-if="isLikelyAnAd">
            Ad detected
        </div>
        <div class="initialcontent" v-else-if="showData === null && firstCaption && currTime >= 0 && currTime < firstCaption.t0">
            <div>Video has <i>{{ showInfo.translation_source }}</i> sentence translations</div>
            <div v-if="showInfo.caption_source === 'hard'">Hanzi provided from OCR, may contain errors</div>
            <br/>
            <q-btn color="primary" label="Go to first subtitle" @click="clickFirst"/>
        </div>
        <div class="initialcontent" v-else-if="showData === null">
            <div>Video has <i>{{ showInfo.translation_source }}</i> sentence translations</div>
            <div v-if="showInfo.caption_source === 'hard'">Hanzi provided from OCR, may contain errors</div>
            <br/>
            <q-btn color="primary" label="Go to next subtitle" @click="clickNext"/>
        </div>
        <CaptionContent
            :class="{ showpeekall: showMenu }"
            v-else
            v-bind:data="showData"
            v-bind:fadeOut="fadeOut"
            v-bind:currTime="currTime"
            v-bind:currentCaptionIdx="currentCaptionIdx"
            v-bind:videoAPI="videoAPI"
        />
        <div ref="pauseProgressBar" v-if="pauseDuration !== null" class="pauseprogressbar" style="width: 50%"></div>
    </div>
</template>

<script>
import CaptionMenu from './CaptionMenu.vue'
import CaptionContent from './CaptionContent.vue'

export default {
    mixins: [mixin],
    props: [
        'currentCaptionIdx',
        'firstCaption',
        'prevCaption',
        'currCaption',
        'nextCaption',
        'currTime',
        'paused',
        'videoAPI',
        'isLoading',
        'isLikelyAnAd',
        'pauseDuration',
    ],
    components: {CaptionContent, CaptionMenu},
    data: function() { return {
        showMenu: false,
        showData: null,
        fadeOut: false,
    }},
    updated: function() {
        const self = this;
        this.$nextTick(function () {
            if (self.pauseDuration !== null) {
                self.$refs.pauseProgressBar.style.transition = `width ${self.pauseDuration}s linear`;
                self.$refs.pauseProgressBar.style.width = '0%';
            }
        });
    },
    methods: {
        mouseOver: function() {
            this.showMenu = true;
            this.$emit('mouseOver');
        },
        mouseOut: function() {
            this.showMenu = false;
        },
        updateFadeout: function() {
            // NOTE: we set fadeOut based on currTime in a watch instead of computed, because a computed makes the component re-render every frame
            this.fadeOut = this.showData !== null && (this.currTime > this.showData.t1 + CAPTION_FADEOUT_TIME || this.currTime < this.showData.t0); // eslint-disable-line
        },
        clickFirst: function() {
            this.videoAPI.setCurrentTime(this.firstCaption.t0 + 1e-3);
            this.videoAPI.play();
            this.$emit('seeked');
        },
        clickNext: function() {
            this.videoAPI.setCurrentTime(this.nextCaption.t0 + 1e-3);
            this.videoAPI.play();
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
    display: inline-block;
    width: 580px;
    text-align: center;
    padding-top: 25px;
    padding-bottom: 25px;
    padding-left: 50px;
    padding-right: 50px;
}

.loadingcontent {
    display: inline-block;
    text-align: center;
    padding-top: 50px;
    padding-bottom: 50px;
    padding-left: 100px;
    padding-right: 100px;
}

.lazybugcaptiondiv {
    color: white !important;
    background-color: rgba(0, 0, 0, 1.0);
    text-align: left;
    font-size: 18px !important;
    padding: 0px;
    min-width: 7em;
}

.lazybugcaptiondiv:not(.docked) {
    filter: drop-shadow(rgb(25, 25, 25) 3px 3px 5px);
    background-color: rgba(0, 0, 0, 0.75);
}

.lazybugcaptiondiv.docked {
    text-align: center;
}

.lazybugcaptiondiv.paused,
.paused .captionmenu{
    background-color: rgba(0, 0, 0, 1.0);
    transition: background-color 300ms linear;
}

.pauseprogressbar {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    height: 5px;
    background-color: green;
    border-radius: 3px;
}

.lazybugcaptiondiv.mobile:not(.paused) .captioncontent {
    display: none;
}
</style>
