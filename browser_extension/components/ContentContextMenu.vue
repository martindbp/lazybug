<template>
    <span class="contextmenu">
        <span v-if="hide" class="contexticon hide" title="Hide" v-html="hideIcon" @click.stop.prevent="clickButton('hide')"></span>
        <span v-if="pin" class="contexticon pin" title="Pin" v-html="pinIcon" @click.stop.prevent="clickButton('pin')"></span>
        <span v-if="dict" class="contexticon dictionary" title="Look up in dictionary" v-html="dictionaryIcon" @click.stop.prevent="clickButton('dict')"></span>
        <span v-if="copy" class="contexticon copy" title="Copy" v-html="copyIcon" @click.stop.prevent="clickButton('copy')"></span>
        <span v-if="star" class="contexticon star" title="Star" v-html="hollowstarIcon" @click.stop.prevent="clickButton('star')"></span>
        <span v-if="unstar" class="contexticon unstar" title="Unstar" v-html="starIcon" @click.stop.prevent="clickButton('unstar')"></span>
        <span v-if="switch" class="contexticon switch" :title="switchlabel" v-html="switchIcon" @click.stop.prevent="clickButton('switch')"></span>
    </span>
</template>

<script>
export default {
    props: ['type', 'idx', 'hide', 'star', 'unstar', 'pin', 'dict', 'copy', 'click', 'switch', 'switchlabel'],
    data: function () { return {
        plusIcon: getIconSvg("math-plus", 18),
        dictionaryIcon: getIconSvg("dictionary", 18),
        hideIcon: getIconSvg("hide", 18),
        pinIcon: getIconSvg("pin", 18),
        copyIcon: getIconSvg("copy", 18),
        starIcon: getIconSvg("star", 18),
        hollowstarIcon: getIconSvg("hollowstar", 18),
        switchIcon: getIconSvg("switch", 18),
    }},
    methods: {
        clickButton: function(action) {
            this.click(action, this.type, this.idx);
        },
    }
};
</script>

<style>

.contextmenu {
    z-index: 999;
    background-color: rgb(50, 50, 50);
    position: absolute;
    right: 0;
    top: -32px;
    font-size: 0;
    padding: 5px;
    border-radius: 3px;
    line-height: 1em;
}

.contexticon svg {
    background-color: rgb(50, 50, 50);
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

</style>
