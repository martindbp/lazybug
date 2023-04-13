<template>
    <span class="contextmenu">
        <span v-if="hide" class="contexticon hide" title="Hide" v-html="hideIcon" @click.stop.prevent="clickButton('hide')"></span>
        <span v-if="pin" class="contexticon pin" title="Pin" v-html="pinIcon" @click.stop.prevent="clickButton('pin')"></span>
        <span v-if="unpin" class="contexticon unpin" title="Unpin" v-html="unpinIcon" @click.stop.prevent="clickButton('unpin')"></span>
        <span v-if="dict" class="contexticon dictionary" title="Look up in dictionary" v-html="dictionaryIcon" @click.stop.prevent="clickButton('dict')"></span>
        <span v-if="copy" class="contexticon copy" title="Copy" v-html="copyIcon" @click.stop.prevent="clickButton('copy')"></span>
        <span v-if="star" class="contexticon star" title="Star" v-html="hollowstarIcon" @click.stop.prevent="clickButton('star')"></span>
        <span v-if="unstar" class="contexticon unstar" title="Unstar" v-html="starIcon" @click.stop.prevent="clickButton('unstar')"></span>
        <span v-if="switchT" class="contexticon switch" title="Unstar" v-html="switchIcon" @click.stop.prevent="clickButton('switch')"></span>
        <span v-if="options" class="contexticon options" title="Options" v-html="optionsIcon" @click.stop.prevent="clickButton('options')"></span>
        <q-badge class="statsbadge" v-if="stats > 0" align="middle" :color="stats === 1 ? 'red' : 'green'" @click.stop.prevent title="Occurrences in video">{{ stats }}</q-badge>
    </span>
</template>

<script>
export default {
    props: {
        type: { default: 'word' },
        idx: { default: null },
        hide: { default: false },
        star: { default: false },
        unstar: { default: false },
        pin: { default: false },
        unpin: { default: false },
        dict: { default: false },
        copy: { default: false },
        options: { default: false },
        stats: { default: 0 },
        switchT: { default: false },
        switchlabel: { default: '' },
        click: { default: null },
    },
    data: function () { return {
        plusIcon: getIconSvg("math-plus", 18),
        dictionaryIcon: getIconSvg("dictionary", 18),
        hideIcon: getIconSvg("hide", 18),
        pinIcon: getIconSvg("pin", 18),
        unpinIcon: getIconSvg("unpin", 18),
        copyIcon: getIconSvg("copy", 18),
        starIcon: getIconSvg("star", 18),
        hollowstarIcon: getIconSvg("hollowstar", 18),
        switchIcon: getIconSvg("switch", 18),
        optionsIcon: getIconSvg("options", 18),
    }},
    methods: {
        clickButton: function(action) {
            this.click(action, this.type, this.idx);
        },
    }
};
</script>

<style>

.captioncard:not(.captioncardhidden):not(.placeholder):not(.mousehasnotmovedafterpeeking):hover .contextmenu {
    visibility: visible;
    opacity: 1.0;
}

.contextmenu {
    z-index: 999;
    background-color: rgb(50, 50, 50);
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: -32px;
    font-size: 0;
    padding: 5px;
    border-radius: 3px;
    line-height: 0;
    visibility: hidden;
    opacity: 0;
    transition: 0.20s;
    transition-delay: 0.125s;
}

.contexticon svg {
    background-color: rgb(50, 50, 50);
}

.contexticon svg {
    width: 22px; /* WHYYY??? */
    height: 22px;
}

#extroot .contexticon svg {
    width: 18px;
    height: 18px;
}

.contexticon:hover {
    filter: brightness(1.5);
}

.contexticon:active {
    filter: brightness(2.5);
}

.contexticon:not(:last-child) {
    margin-right: 3px;
}

.contexticon > svg {
    border-radius: 3px;
    padding: 2px;
}

.nonhanzi .contextmenu {
    display: none;
}

.statsbadge {
    margin-top: -3px;
}

</style>
