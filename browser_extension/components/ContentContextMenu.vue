<template>
    <span class="contextmenu">
        <span v-if="know" class="contexticon know" title="Know this" v-html="checkIcon" @click.stop.prevent="clickButton('know')"></span>
        <span v-if="learn" class="contexticon learn" title="Learn this" v-html="plusIcon" @click.stop.prevent="clickButton('learn')"></span>
        <span v-if="reset" class="contexticon remove" title="Reset to unknown" v-html="undoIcon" @click.stop.prevent="clickButton('remove')"></span>
        <span v-if="dict" class="contexticon dictionary" title="Look up in dictionary" v-html="dictionaryIcon" @click.stop.prevent="clickButton('dict')"></span>
    </span>
</template>

<script>
export default {
    props: ['type', 'idx', 'know', 'learn', 'reset', 'dict', 'click'],
    data: function () { return {
        plusIcon: getIconSvg("math-plus", 18),
        dictionaryIcon: getIconSvg("dictionary", 18),
        checkIcon: getIconSvg("check", 18),
        undoIcon: getIconSvg("undo", 18),
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

.contexticon.know svg {
    background: limegreen;
}

.contexticon.remove svg {
    background: red;
}

.contexticon.dictionary svg {
    background: #483D8B;
}

.contexticon > svg {
    border-radius: 3px;
    padding: 2px;
}

</style>
