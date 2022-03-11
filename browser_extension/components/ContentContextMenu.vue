<template>
    <span class="contextmenu">
        <span v-if="hide" class="contexticon hide" title="Hide" v-html="hideIcon" @click.stop.prevent="clickButton('hide')"></span>
        <span v-if="pin" class="contexticon pin" title="Pin" v-html="pinIcon" @click.stop.prevent="clickButton('pin')"></span>
        <span v-if="learn" class="contexticon learn" title="Learn" v-html="plusIcon" @click.stop.prevent="clickButton('learn')"></span>
        <span v-if="unlearn" class="contexticon unlearn" title="Unlearn" v-html="undoIcon" @click.stop.prevent="clickButton('unlearn')"></span>
        <span v-if="dict" class="contexticon dictionary" title="Look up in dictionary" v-html="dictionaryIcon" @click.stop.prevent="clickButton('dict')"></span>
    </span>
</template>

<script>
export default {
    props: ['type', 'idx', 'hide', 'learn', 'pin', 'dict', 'click'],
    data: function () { return {
        plusIcon: getIconSvg("math-plus", 18),
        dictionaryIcon: getIconSvg("dictionary", 18),
        hideIcon: getIconSvg("hide", 18),
        undoIcon: getIconSvg("undo", 18),
        pinIcon: getIconSvg("pin", 18),
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
    left: 0;
    top: -32px;
    font-size: 0;
    padding: 5px;
    border-radius: 3px;
    line-height: 1em;
}

.contexticon:hover {
    filter: brightness(1.5);
}

.contexticon:not(:last-child) {
    margin-right: 3px;
}

.contexticon.learn svg {
    background: darkorange;
}

.contexticon.hide svg {
    background: limegreen;
}

.contexticon.pin svg {
    background: lightgray;
}

.contexticon.unlearn svg {
    background: darkorange;
}

.contexticon.dictionary svg {
    background: #483D8B;
}

.contexticon > svg {
    border-radius: 3px;
    padding: 2px;
}

</style>
