<template>
    <div id="popupcontainer">
        <div style="position: relative; text-align: right">
            <q-toggle
                 style="position: fixed; left: 0;"
                 v-model="extensionToggle"
                 color="green"
            />
            <q-btn-dropdown color="primary" label="Go to">
                <q-list>
                    <q-item v-for="video in recent" clickable @click="clickRecent(video)">
                        <q-item-section>
                            <q-item-label> {{ videoLabel(video) }} </q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
        </div>
        <q-btn flat label="Dashboard" @click="dashboard" />
        <div v-if="dev">
            <q-btn flat label="Measure caption" @click="measureCaption" />
            <q-btn flat label="Print playlist" @click="printPlaylist" />
        </div>
        <a href="https://www.patreon.com/martindbp">Donate</a>
    </div>
</template>

<script>
export default {
    props: {
    },
    data: function() { return {
        extensionToggle: window.localStorage.getItem('extensionToggle') === 'true',
        dev: ZIMUDEVMODE,
        showList: null,
        recent: null,
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
            self.recent.push({ captionId: 'random' });
        });
    },
    methods: {
        videoLabel: function(video) {
            if (video.captionId === 'random') return "Random Show";
            return `${resolveShowName(video.showName) || ''} ${video.seasonName || ''} ${video.episodeName || ''}`;
        },
        clickRecent: function(video) {
            if (video.captionId === 'random') return this.random();

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
        random: function() {
            if (this.showList === null) return;

            const showNames = Object.keys(this.showList).filter((name) => this.showList[name].released);
            const showName = showNames[Math.floor(Math.random() * showNames.length)];
            const data = this.showList[showName];
            const firstEpisode = data.seasons[0].episodes[0].id;
            const [tmp, videoId] = firstEpisode.split('youtube-');
            chrome.tabs.create({
                url: `https://youtube.com/watch?v=${videoId}`,
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

#popuproot {
    width: 200px;
    min-height: 250px;
}

</style>
