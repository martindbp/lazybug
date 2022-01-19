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
    background: none;
    color: inherit;
    border: none;
    padding: 0;
    font: inherit;
    cursor: pointer;
    outline: inherit;
}

.svgbutton > svg {
    width: 30px;
    height: 30px;
}

.svgbutton:hover {
    background-color: gray;
}

.svgbutton:active {
    background-color: lightgray;
}
</style>
