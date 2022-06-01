<template>
    <div id="popupcontainer">
        <q-toggle
          v-model="extensionToggle"
          color="green"
        />
        <q-btn-dropdown color="primary" label="Go">
            <q-list>
                <q-item v-for="video in recent" clickable @click="clickRecent(video)">
                    <q-item-section>
                        <q-item-label> {{ videoLabel(video) }} </q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-btn-dropdown>
        <q-btn label="Dashboard" @click="dashboard" />
        <q-btn label="I'm feeling lucky" @click="imFeelingLucky" :loading="feelingLuckyLoading" />
        <div v-if="dev">
            <q-btn label="Measure caption" @click="measureCaption" />
            <q-btn label="Print playlist" @click="printPlaylist" />
        </div>
        <a href="https://www.patreon.com/martindbp">Donate</a>
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
        showList: null,
        recent: null,
        feelingLuckyLoading: false,
    }},
    mounted: function() {
        const self = this;
        getIndexedDbData('other', ['options'], function (data) {
            let setVal = true;
            if (data[0]) {
                setVal = data[0].extensionToggle;
            }
            self.extensionToggle = setVal;
        });

        fetchVersionedResource('show_list.json', function (data) {
            if (data === 'error') {
                return;
            }
            else {
                self.showList = data;
            }
        });

        getRecent(function(data) {
            const videos = [];
            self.recent = data;
        });
    },
    methods: {
        videoLabel: function(video) {
            return `${resolveShowName(video.showName) || ''} ${video.seasonName || ''} ${video.episodeName || ''}`;
        },
        clickRecent: function(video) {
            const parts = video.captionId.split('-');
            const id = parts.slice(1).join('-');
            const url = `https://youtube.com/watch?v=${id}`;
            chrome.tabs.create({
                url: url
            });
        },
        dashboard: function() {
            chrome.tabs.create({
                url: "dashboard.html",
            });
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
        imFeelingLucky: function() {
            if (this.showList === null) return;

            this.feelingLuckyLoading = true;

            const showName = this.showList[Math.floor(Math.random() * this.showList.length)];
            const self = this;
            fetchResource(`shows/${showName}.json`, function (data) {
                self.feelingLuckyLoading = false;
                if (data === 'error') {
                    alert('Error while fetching show info');
                }
                else {
                    const firstEpisode = data.seasons[0].episodes[0].id;
                    const [tmp, videoId] = firstEpisode.split('youtube-');
                    chrome.tabs.create({
                        url: `https://youtube.com/watch?v=${videoId}`,
                    });
                }
            });

        }
    },
    watch: {
        extensionToggle: function(newValue) {
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

#popupcontainer {
    text-align: center;
}

</style>
