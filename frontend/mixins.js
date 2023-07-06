function combinations(options, accumulatorArray, currCombination = [], currIdx = 0) {
    if (currIdx === options.length) {
        accumulatorArray.push(currCombination);
        return;
    }

    for (const item of options[currIdx]) {
        //let newCombination = [...currCombination];
        let newCombination = currCombination.concat(item);
        combinations(options, accumulatorArray, newCombination, currIdx + 1);
    }
}

const mixin = {
    data: function() { return {
        accountCallback: null,
    }},
    watch: {
        applicationReady: function() {
            let $el = document.querySelector('.loading-container');
            if ($el) {
                $el.remove()
            }
        },
        accessTokenPlusNeedSync: function() {
            if (this.accessToken && this.accountCallback && !this.needSync) {
                this.accountCallback();
                this.accountCallback = null;
            }
        },
        showInfo: function(newData, oldData) { // fetch Discourse comments for show
            if (
                this.season === null ||
                this.episode === null
            ) {
                return;
            }

            if (newData && oldData && newData.showId === oldData.showId) return;

            const showId = this.showInfo.showId;
            const topicId = this.showInfo.discourse_topic_id;
            if (this.$store.state.discourseCommentsForShow === topicId) return; // already fetching
            const message = {
                type: 'getDiscourseTopicComments',
                data: topicId,
                // Following fields are for testing
                showId: this.showId,
                season: this.season,
                episode: this.episode,
            };
            const self = this;
            self.$store.commit('setShowDiscourseComments', topicId);  // set as fetching
            sendMessageToBackground(message, function(data) {
                if (data === 'error') {
                    self.$store.commit('setShowDiscourseComments', 'error');
                    return;
                }
                if (self.showInfo && self.showInfo.showId !== showId) return; // show changed, discard this fetch
                self.$store.commit('setShowDiscourseComments', data);
            }, false); // don't notify failure
        },
    },
    methods: {
        getSeasonName: function(i) {
            if (
                this.season === null ||
                this.episode === null
            ) {
                return;
            }
            return getSeasonName(this.showInfo, i);
        },
        getEpisodeName: function(i) {
            if (
                this.season === null ||
                this.episode === null
            ) {
                return;
            }
            return getEpisodeName(this.showInfo, this.season, i);
        },
        showAccountModalWithCallback: function(callback = null) {
            this.$store.commit('setShowDialog', {dialog: 'account', value: 'login'});
            this.accountCallback = callback;
        },
        showModalAndSync: function(closeAfterDone = false, callback = null, syncIsAfterLogin = false) {
            this.$store.commit('setShowDialog', {dialog: 'sync', value: true});
            const self = this;
            this.syncDatabase(function(error) {
                if (! error && closeAfterDone) {
                    // Close after some delay
                    if (self.$store.state.syncError) return; // don't close if there's an error

                    setTimeout(function() {
                        self.$store.commit('setShowDialog', {dialog: 'sync', value: false});
                    }, 500);
                }
                if (callback) callback(error);
            }, syncIsAfterLogin);
        },
        exportUploadDatabase: function(callback) {
            const self = this;
            exportDatabaseJson(function(data) {
                data = JSON.stringify(data);
                self.getLinkAndUploadData(data, callback);
            });
        },
        getLinkAndUploadData: function(data, callback) {
            const self = this;
            const accessToken = this.$store.state.accessToken;
            self.$store.commit('addSyncProgress', 'Getting signed upload link');
            getSignedUploadLink(accessToken, data.length, function(url, error) {
                if (error) {
                    callback(error);
                    return;
                }

                self.$store.commit('addSyncProgress', 'Uploading data');
                uploadData(url, data, accessToken, function(error) {
                    if (error) {
                        callback(error);
                        return;
                    }
                    self.$store.commit('addSyncProgress', 'Getting uploaded timestamp');
                    getDatabaseLastModifiedDate(accessToken, function(serverLastSyncDateString, error) {
                        if (error) {
                            self.$store.commit('setSyncDone', error);
                            callback(error);
                            return;
                        }
                        self.$store.commit('addSyncProgress', `New timestamp: ${serverLastSyncDateString}`);
                        self.$store.commit('setLastSyncDate', serverLastSyncDateString);
                        self.$store.commit('addSyncProgress', 'Successfully uploaded');
                        callback(); // success
                    });
                });
            });
        },
        downloadDatabase: function(callback) {
            const self = this;
            this.$store.commit('addSyncProgress', 'Getting signed download link');
            getSignedDownloadLink(this.$store.state.accessToken, function(url) {
                self.$store.commit('addSyncProgress', 'Downloading data...');
                downloadData(url, function(data, error) {
                    if (error) callback(null, error);
                    else {
                        self.$store.commit('addSyncProgress', 'Successfully downloaded');
                        callback(data, null);
                    }
                });
            });
        },
        syncDatabase: function(callback, syncIsAfterLogin = false) {
            const self = this;
            const accessToken = this.$store.state.accessToken;
            let lastSyncDateString = this.$store.state.lastSyncDate;
            let lastSyncDate = null;
            if (lastSyncDateString !== null) lastSyncDate = Date.parse(lastSyncDateString);
            this.$store.commit('setSyncProgress', ['Checking server data modified date']);
            this.$store.commit('setSyncError', null);
            this.$store.commit('setIsSyncing', true);
            getDatabaseLastModifiedDate(accessToken, function(serverLastSyncDateString, error) {
                if (error) {
                    self.$store.commit('setSyncDone', error);
                    callback(error);
                    return;
                }
                self.$store.commit('addSyncProgress', `Server last modified ${serverLastSyncDateString}`);
                const serverLastSyncDate = serverLastSyncDateString === null ? null : Date.parse(serverLastSyncDateString);
                if (serverLastSyncDate !== null && (serverLastSyncDate > lastSyncDate || lastSyncDate === null)) {
                    // Server date is newer, download, merge and upload
                    self.$store.commit('addSyncProgress', `Server date is newer (local = ${lastSyncDateString})`);
                    self.downloadDatabase(function(remoteData, error) {
                        if (error) {
                            self.$store.commit('setSyncDone', error);
                            return callback(error);
                        }

                        // If local database has an older version than remote, we need to reload application, not merge
                        if (remoteData.data.databaseVersion > getLatestDbVersion()) {
                            const error = 'Local database is older version than remote, please reload app';
                            self.$store.commit('setSyncDone', error);
                            return callback(error);
                        }

                        if (! self.$store.state.needSync) {
                            self.$store.commit('addSyncProgress', 'No new local data to merge');
                            self.$store.commit('setLastSyncDate', serverLastSyncDateString);

                            self.$store.commit('addSyncProgress', 'Importing server database');
                            importDatabaseJson(remoteData, self.$store, function(error) {
                                self.$store.commit('setSyncDone', error);
                                if (error) {
                                    return callback(error);
                                }

                                self.$store.commit('addSyncProgress', 'Server database successfully imported');
                                return callback();
                            });
                            return;
                        }

                        self.$store.commit('addSyncProgress', `Upgrading remote database from version ${remoteData.data.databaseVersion} to ${getLatestDbVersion()} before merging`);
                        upgradeDatabase(remoteData, function(upgradedRemoteData, error) {
                            if (error) {
                                const errorMessage = `Upgrading remote database failed: ${error}`;
                                self.$store.commit('setSyncDone', errorMessage);
                                return callback(error);
                            }
                            else {
                                remoteData = upgradedRemoteData;
                            }

                            // Get local database json
                            self.$store.commit('addSyncProgress', 'Local database has new data, exporting');
                            exportDatabaseJson(function(localData) {
                                self.$store.commit('addSyncProgress', 'Merging local and remote database');

                                // Merge
                                const localLogIdx = localData.data.tables.map((table) => table.name).indexOf('log');
                                const remoteLogIdx = remoteData.data.tables.map((table) => table.name).indexOf('log');

                                // Concat and sort log sessions
                                const sessions = {};
                                const numLocalSessions = localData.data.data[localLogIdx].rows.length;
                                localData.data.data[localLogIdx].rows.forEach((row) => sessions[row.sessionTime] = row);
                                remoteData.data.data[remoteLogIdx].rows.forEach((row) => sessions[row.sessionTime] = row);
                                localData.data.data[localLogIdx].rows = Object.values(sessions).sort((a, b) => a.sessionTime - b.sessionTime);
                                const numLocalSessionsAfterMerge = localData.data.data[localLogIdx].rows.length;
                                self.$store.commit('addSyncProgress', `Added ${numLocalSessionsAfterMerge - numLocalSessions} sessions from remote`);

                                // For other (like options) take those with newest timestamp (if logged in)
                                const localOtherIdx = localData.data.tables.map((table) => table.name).indexOf('other');
                                const remoteOtherIdx = remoteData.data.tables.map((table) => table.name).indexOf('other');
                                const localOther = localData.data.data[localOtherIdx].rows;
                                const remoteOther = localData.data.data[remoteOtherIdx].rows;
                                const other = {};
                                localData.data.data[localOtherIdx].rows.forEach((row) => other[row.id] = row);
                                remoteData.data.data[remoteOtherIdx].rows.forEach((row) => {
                                    if (!syncIsAfterLogin && other[row.id] && row.timestamp < other[row.id].timestamp) {
                                        self.$store.commit('addSyncProgress', `Kept more recent local data for other ${row.id} data`);
                                        return; // keep local
                                    }
                                    self.$store.commit('addSyncProgress', `Kept more recent remote data for other ${row.id} data`);
                                    other[row.id] = row;
                                });

                                localData.data.data[localOtherIdx].rows = Object.values(other);

                                // For states, we need to merge based on explicit references/implicit count
                                const localStatesIdx = localData.data.tables.map((table) => table.name).indexOf('states');
                                const remoteStatesIdx = remoteData.data.tables.map((table) => table.name).indexOf('states');
                                const localStatesDict = {};
                                for (const localItem of localData.data.data[localStatesIdx].rows) {
                                    localStatesDict[localItem.id] = localItem;
                                }

                                let mergedStates = 0;
                                let remoteOnlyStates = 0;
                                for (let remoteItem of remoteData.data.data[remoteStatesIdx].rows) {
                                    if (localStatesDict[remoteItem.id]) {
                                        const key = remoteItem.id
                                        const localItem = localStatesDict[key];
                                        // Merge the two rows
                                        const remoteExplicit = remoteItem.value[2];
                                        const localExplicit = localItem.value[2];
                                        if (localExplicit && remoteExplicit) {
                                            // Use newest
                                            const useItem = localItem.timestamp > remoteItem.timestamp ? localItem : remoteItem;
                                            localStatesDict[key].value[0] = useItem.value[0];
                                            localStatesDict[key].value[1] = useItem.value[1];
                                        }
                                        else if (localExplicit) {
                                            // Use local values
                                            for (let i = 0; i < 3; i++) localStatesDict[key].value[i] = localItem.value[i];
                                        }
                                        else if (remoteExplicit) {
                                            // Use remote values
                                            for (let i = 0; i < 3; i++) localStatesDict[key].value[i] = remoteItem.value[i];
                                        }
                                        else {
                                            // Neither is explicit, so take max
                                            for (let i = 0; i < 2; i++) {
                                                localStatesDict[key].value[i] = Math.max(remoteItem.value[i], localItem.value[i]);
                                            }
                                        }

                                        mergedStates++;
                                    }
                                    else {
                                        localStatesDict[remoteItem.id] = remoteItem; // just assign since local doesn't have it
                                        remoteOnlyStates++;
                                    }
                                }
                                localData.data.data[localStatesIdx].rows = Object.values(localStatesDict);
                                self.$store.commit('addSyncProgress', `Merged ${mergedStates} states, added ${remoteOnlyStates} new states from remote`);
                                self.$store.commit('addSyncProgress', 'Merge done, importing merged database');

                                importDatabaseJson(localData, self.$store, function(error) {
                                    if (error) {
                                        self.$store.commit('setSyncDone', error);
                                        return callback(error);
                                    }

                                    self.$store.commit('addSyncProgress', 'Uploading merged database');
                                    const data = JSON.stringify(localData);
                                    // Upload
                                    self.getLinkAndUploadData(data, function(error) {
                                        if (error) {
                                            self.$store.commit('setSyncDone', error);
                                            return callback(error);
                                        }

                                        self.$store.commit('setSyncDone', null);
                                        return callback();
                                    });
                                });

                            });

                        });
                    });
                }
                else if (serverLastSyncDate !== null && serverLastSyncDate === lastSyncDate && ! self.$store.state.needSync) {
                    // The server date is the same as local, don't upload
                    self.$store.commit('addSyncProgress', 'Server date is is same as local data and no local changes, not uploading');
                    self.$store.commit('setSyncDone', null);
                    return callback();
                }
                else {
                    // Server date is older or same as previously synced (or doesn't exist)
                    // or we have new local changes, so just upload
                    self.$store.commit('addSyncProgress', `Server date is same or older (or doesn't exist) (local=${lastSyncDateString}), uploading our local data`);
                    self.exportUploadDatabase(function(error) {
                        if (error) {
                            self.$store.commit('setSyncDone', error);
                            return callback(error);
                        }

                        self.$store.commit('setSyncDone', null);
                        return callback();
                    });
                }
            });
        },
        setPlaying: function(showId, seasonIdx = 0, episodeIdx = 0) {
            this.$store.commit('setPlayerData', {playerId: 'player', showId: showId});
            const showInfo = getShowInfo('player', this.$store);
            if (showInfo.embeddable === false) {
                this.$store.commit('setNonEmbeddableVideoSelected', this.showInfo);
                this.$store.commit('setPlayerData', {playerId: 'player', showId: null});
                if (this.$store.state.hasLazybugExtension) {
                    this.goExternal();
                }
                else {
                    this.$store.commit('setShowDialog', {dialog: 'embeddable', value: true});
                }
                return;
            }
            this.$store.commit('setPlayerData', {playerId: 'player', season: seasonIdx, episode: episodeIdx});
            const showList = this.$store.state.showList;
            this.$store.commit('setCaptionId', {playerId: 'player', value: showList[showId].seasons[seasonIdx].episodes[episodeIdx].id});
            if (BROWSER_EXTENSION) {
                document.location = this.getVideoURL(seasonIdx, episodeIdx);
            }
            else {
                this.$store.commit('setPage', 'player');
            }
        },
        goExtensionInstall: function() {
            window.open(EXTENSION_INSTALL_URL, '_blank').focus();
        },
        goLazybug: function() {
            window.open(LAZYBUG_URL, '_blank').focus();
        },
        goExternal: function() {
            const showInfo = this.$store.state.nonEmbeddableVideoSelected;
            const captionId = showInfo.seasons[0].episodes[0].id;
            const videoId = videoIdFromCaptionId(captionId);
            const site = siteFromCaptionId(captionId);
            const template = this.$store.state.STRINGS.site[site].urlTemplates.videoId;
            const url = template.replace('${id}', videoId);
            window.open(url, '_blank').focus();
            this.$store.commit('setNonEmbeddableVideoSelected', null);
            this.$store.commit('setShowDialog', {dialog: 'embeddable', value: false});
        },
        getVideoURL: function(seasonIdx, episodeIdx) {
            const videoId = videoIdFromCaptionId(this.captionId);
            const template = this.getSiteString('urlTemplates').videoId;
            const url = template.replace('${id}', videoId);
            return url;
        },
        sm2tr(text, optionsOverride = true) {
            if (this.$store.state.DICT === null) return null;
            if (optionsOverride && this.$store.state.options.characterSet == 'sm') return text;

            let trText = '';
            let nextIdx = 0;
            while (nextIdx < text.length) {
                let foundStr = text.substring(nextIdx, nextIdx+1);
                for (var i = nextIdx+1; i < text.length; i++) {
                    const subStr = text.substring(nextIdx, i);
                    if (this.$store.state.DICT[foundStr] !== undefined) {
                        break;
                    }
                    foundStr = subStr;
                }
                let entries = this.$store.state.DICT[foundStr];
                if (entries !== undefined) {
                    trText += dictArrayToDict(entries[0]).hzTrad;
                }
                else {
                    trText += foundStr;
                }

                nextIdx += foundStr.length;
            }

            return trText;
        },
        appendSessionLog(data) {
            appendSessionLog(this.playerId, this.$store, data);
        },
        createSession() {
            createSession(this.$store.state);
        },
        getLvlStates: function(type, greaterThan, level) {
            if (this.$store.state.DICT === null || this.$store.state.HSK_WORDS === null) return {};
            const d = this.$store.state.DICT;
            const states = {};
            for (let lvl = 1; lvl <= 6; lvl++) {
                let apply = false;
                if (greaterThan) apply = lvl > level;
                else apply = lvl <= level;

                if (!apply) continue;

                for (const hz of this.$store.state.HSK_WORDS[lvl-1]) {
                    let entries = d[hz];
                    let entryPys = [];
                    if (entries === undefined) {
                        // No entry, so pick all combinations of single char pys
                        const charPyOptions = [];
                        for (const c of hz) {
                            const charEntryPys = [];
                            for (let entry of d[c]) {
                                charEntryPys.push(dictArrayToDict(entry).pys)
                            }
                            charPyOptions.push(charEntryPys);
                        }
                        combinations(charPyOptions, entryPys);
                    }
                    else {
                        for (const entry of entries) {
                            entryPys.push(dictArrayToDict(entry).pys);
                        }
                    }

                    for (const pys of entryPys) {
                        applyState(d, states, type, hz, pys, null, null, StateHidden, StateHidden, true, false);
                    }
                }
            }
            return states;
        },
        getSiteString: function(name) {
            if (this.$store.state.STRINGS === null) return null;
            return this.$store.state.STRINGS.site[this.site][name];
        },
        addBadge: function($img) {
            // For browser extension only
            if ($img === null) return;
            const $a = $img.closest("#thumbnail");
            const youtubeIdRegex = /^.*\?v\=([a-zA-Z0-9_-]*)&?.*/;
            const match = youtubeIdRegex.exec($a.href);
            if (!match) return;

            const id = match[1];
            if (! this.$store.state.videoList.has(`youtube-${id}`)) {
                return;
            }

            $img.style.position = 'relative';
            const badge = document.createElement('img');
            badge.classList.add('lazybugbadge');
            badge.src = CDN_URL + 'lazybug-public/images/64_lazybug.png';
            badge.style.filter = 'drop-shadow(5px 5px 5px black)';
            badge.style.width = badge.style.height = '28px';
            badge.style.position = 'absolute';
            badge.style.top = '4px';
            badge.style.left = '4px';
            $img.parentNode.appendChild(badge);
        },
        initializeThumbnailBadges: function() {
            if (! BROWSER_EXTENSION) return;

            if (this.site !== 'youtube') return null;

            for (const $img of document.querySelectorAll('#thumbnail img:not(.lazybugbadge)')) {
                addBadge($img);
            }

            return new MutationObserver((mutations) => {
                let hasNewThumbnails = false;
                for (let mutation of mutations) {
                    switch(mutation.type) {
                        case 'childList':
                            for (let node of mutation.addedNodes) {
                                if (node.nodeType !== 1) continue;
                                if (node.tagName === 'IMG' && !node.classList.contains('lazybugbadge') && node.closest('#thumbnail')) {
                                    addBadge(node);
                                }
                                else if (node.id === 'thumbnail') {
                                    addBadge(node.querySelector('img:not(.lazybugbadge)'));
                                }
                            }
                            break;
                        case 'attributes':
                            if (mutation.target.id === 'thumbnail' && mutation.attributeName === 'href' && mutation.oldValue !== null) {
                                const $img = mutation.target.querySelector('img:not(.lazybugbadge)');
                                for (const $badgeImg of mutation.target.querySelectorAll('img.lazybugbadge')) {
                                    $badgeImg.remove();
                                }
                                addBadge($img);
                            }
                            break;
                    }
                }
            }).observe(document, {subtree: true, childList: true, attributes: true, attributeOldValue: true});
        },
    },
    computed: {
        currentCaptionIdx: function() {
            const idx = this.captionIdx;
            return Array.isArray(idx) ? idx[0] : idx;
        },
        site: function() {
            if (this.$store.state.STRINGS === null) return null;
            return this.$store.state.STRINGS.urls[document.location.hostname];
        },
        discourseURL: function() {
            return DISCOURSE_URL;
        },
        applicationReady: function() {
            return this.$store.state.cssLoaded && this.$store.state.fetchedAllPublicResources;
        },
        playerData: function() {
            if (!this.playerId) return null;
            return this.$store.state.playerData[this.playerId];
        },
        showInfo: function() {
            if (!this.playerId || !this.playerData) return null;
            const info = getShowInfo(this.playerId, this.$store);
            return info;
        },
        showName: function() {
            if (!this.showInfo || ! this.showInfo.name) return null;
            if (typeof this.showInfo.name === 'object') {
                return `${this.showInfo.name.hz} - ${this.showInfo.name.en}`;
            }
            return this.showInfo.name;
        },
        season: {
            get: function() { return this.playerId ? this.playerData.season : null; },
            set: function(val) { this.$store.commit('setPlayerData', {playerId: this.playerId, season: val}); },
        },
        episode: {
            get: function() { return this.playerId ? this.playerData.episode : null; },
            set: function(val) { this.$store.commit('setPlayerData', {playerId: this.playerId, episode: val}); },
        },
        captionIdx: {
            get: function() { return this.playerData ? this.playerData.captionIdx : null; },
            set: function(val) { this.$store.commit('setPlayerData', {playerId: this.playerId, captionIdx: val}); },
        },
        seasonName: function() {
            return getSeasonName(this.showInfo, this.season);
        },
        episodeName: function() {
            return getSeasonName(this.showInfo, this.season);
        },
        captionId: function() {
            return this.playerData ? this.playerData.captionId : null;
        },
        captionData: function() {
            return this.playerData ? this.playerData.captionData : null;
        },
        captionHash: function() {
            return this.playerData ? this.playerData.captionHash : null;
        },
        navigateToCaptionIdx: function() {
            return this.playerData ? this.playerData.navigateToCaptionIdx : null;
        },
        videoAPI: function() {
            return this.playerData ? this.playerData.videoAPI : null;
        },
        videoDuration: function() {
            return this.playerData ? this.playerData.videoDuration : null;
        },
        sessionTime: function() {
            return this.playerData ? this.playerData.sessionTime : null;
        },
        submittedExercises: function() {
            return this.playerData ? this.playerData.submittedExercises : null;
        },
        AVElement: function() {
            return this.playerData ? this.playerData.AVElement : null;
        },
        accessTokenPlusNeedSync: function() {
            return `${this.accessToken}|${this.needSync}`;
        },
        accessToken: function() {
            return this.$store.state.accessToken;
        },
        needSync: function() {
            return this.$store.state.needSync;
        },
        isMobile: function() {
            return Quasar.Platform.is.mobile === true;
        },
        isExtension: function() {
            return this.$store.state.isExtension;
        },
        isDesktop: function() {
            return Quasar.Platform.is.desktop === true;
        },
        showPercentKnown: function() {
            const personalFilter = this.$store.state.bloomFilter;
            const showBloomFilters = this.$store.state.showBloomFilters;
            if (this.$store.state.accessToken === null) return null
            if (personalFilter === null || showBloomFilters === null) return 0;
            const percentKnown = {};
            for (const key of Object.keys(showBloomFilters.shows)) {
                const show = showBloomFilters.shows[key];
                const bloom = show.bloom;
                //console.log(key, personalFilter.size(), bloom.size(), bloom.intersectionCount(personalFilter));
                //console.log('new vocab per line', (bloom.size() - bloom.intersectionCount(personalFilter)) / show.num_lines);
                //console.log('new vocab per hour line time', (bloom.size() - bloom.intersectionCount(personalFilter)) / (show.sum_line_time / 3600));
                //console.log('new vocab per hour video', (bloom.size() - bloom.intersectionCount(personalFilter)) / (show.sum_video_time / 3600));
                //console.log('percent vocab known', bloom.intersectionCount(personalFilter) / bloom.size());
                percentKnown[key] = bloom.intersectionCount(personalFilter) / bloom.size();
            }
            return percentKnown;
        },
        hideWordsLevelStates: function() {
            return this.getLvlStates('word', false, this.$store.state.options.hideWordsLevel);
        },
        videoWordStats: function() {
            if (this.captionData === null) return {};
            const wordStats = {};
            for (let idx = 0; idx < this.captionData.lines.length; idx++) {
                let line = this.captionData.lines[idx];
                line = captionArrayToDict(this.captionData.lines, idx, this.captionData);
                for (let alignment of line.alignments) {
                    const hz = alignment[2];
                    const py = alignment[3].map((item) => item[0]).join('');
                    const key = `${hz}-${py}`;
                    if (wordStats[key] === undefined) {
                        wordStats[key] = 0;
                    }
                    wordStats[key] += 1;
                }
            }

            return wordStats;
        },
        purePeekStates: function() {
            // We might have set a peek state on an item that is not hidden (e.g. peek row), filter these out
            const states = JSON.parse(JSON.stringify(this.$store.state.peekStates));
            states['translation'] = states['translation'] && this.hiddenStates['translation'];
            for (var i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = (
                        ([true, 'temporaryPeek'].includes(states[type][i]) || states.rows[type])
                        && this.hiddenStates[type][i]
                    );
                }
            }
            return states;
        },
        videoComments: function() {
            const c = this.$store.state.discourseCommentsForShow;
            if ([null, undefined, 'error'].includes(c) || Number.isInteger(c)) return;
            // Look for a link to this video
            let regex = `https://lazybug\.ai/${this.showId}/${this.season+1}/${this.episode+1}.*`;
            return c.filter((post) => post.cooked.match(regex) !== null);
        },
        captionComments: function() {
            const c = this.$store.state.discourseCommentsForShow;
            if ([null, undefined, 'error'].includes(c) || Number.isInteger(c)) return;
            let captionIdx = this.captionIdx;
            if (captionIdx === null) return [];
            if (Array.isArray(captionIdx)) captionIdx = captionIdx[0];
            if (captionIdx === null) return []; // could be null again if before first caption
            // Look for a link to this caption
            let regex = `https://lazybug\.ai/${this.showId}/${this.season+1}/${this.episode+1}/${this.captionIdx+1}.*`;
            return c.filter((post) => post.cooked.match(regex) !== null);
        },
    },
};
