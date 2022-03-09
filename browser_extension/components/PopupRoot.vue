<template>
    <div>
        <q-toggle
          v-model="extensionToggle"
          color="green"
        />
        <div v-if="dev">
            <q-btn label="Dashboard" @click="dashboard" />
            <q-btn label="Measure caption" @click="measureCaption" />
            <q-btn label="Print playlist" @click="printPlaylist" />
        </div>
    </div>
</template>

<script>
const ZIMUDEVMODE = true;
export default {
    props: {
    },
    data: function() { return {
        extensionToggle: window.localStorage.getItem('extensionToggle') === 'true',
        dev: ZIMUDEVMODE,
    }},
    mounted: function() {
        const self = this;
        getIndexedDbData('other', ['options'], function (data) {
            if (data[0]) {
                self.extensionToggle = data[0].extensionToggle;
                self.updateBadge();
            }
        });
    },
    methods: {
        dashboard: function() {
            chrome.tabs.create({
              url: "dashboard.html",
            });
        },
        updateBadge: function() {
            if (this.extensionToggle) {
                chrome.action.setBadgeText({text:''});
            }
            else {
                chrome.action.setBadgeBackgroundColor({color:[255, 0, 0, 255]});
                chrome.action.setBadgeText({text:'OFF'});
            }
        },
        measureCaption: function() {
            chrome.tabs.query({active: true, lastFocusedWindow: true}, tabs => {
                tabs.forEach(tab => {
                    chrome.tabs.sendMessage(tab.id, 'measurecaption');
                });
            });
        },
        printPlaylist: function() {
            chrome.tabs.query({active: true, lastFocusedWindow: true}, tabs => {
                tabs.forEach(tab => {
                    chrome.tabs.sendMessage(tab.id, 'printplaylist');
                });
            });
        },
    },
    watch: {
        extensionToggle: function(newValue) {
            this.updateBadge();
            window.localStorage.setItem('extensionToggle', newValue);
            chrome.tabs.query({}, function(tabs) {
                for (const tab of tabs) {
                    chrome.tabs.sendMessage(tab.id, {type: "extensionToggle", data: newValue});
                }
            });
        },
    },
};
</script>

<style>
</style>
