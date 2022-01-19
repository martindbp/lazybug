<template>
    <button
        v-on="$listeners"
        class="svgbutton"
        v-html="iconsvg">
    </button>
</template>

<script>
const ICON_SIZE = 24;

export default {
    props: ['name', 'click'],
    computed: {
        iconsvg: function() {
            return getIconSvg(this.name, ICON_SIZE);
        }
    }
};
</script>

<style>
.svgbutton {
    position: relative;
    background: none;
    color: inherit;
    border: none;
    padding: 0;
    margin: 0;
    font: inherit;
    cursor: pointer;
    outline: inherit;
    width: 30px;
    height: 30px;
}

.svgbutton > svg {
    width: 24px;
    height: 24px;
    position: absolute;
    top: 50%;
    lefT: 50%;
    margin-top: -12px;
    margin-left: -12px;
}

.svgbutton:hover {
    background-color: gray;
}

.svgbutton:active {
    background-color: lightgray;
}
</style>
