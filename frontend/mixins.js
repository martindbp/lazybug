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
        accessTokenPlusNeedSync: function() {
            if (this.accessToken && this.accountCallback && !this.needSync) {
                this.accountCallback();
                this.accountCallback = null;
            }
        },
    },
    methods: {
        getSeasonName: function(i) {
            return getSeasonName(this.showInfo, i);
        },
        getEpisodeName: function(i) {
            return getEpisodeName(this.showInfo, this.season, i);
        },
        showAccountModalWithCallback: function(callback = null) {
            this.$store.commit('setShowDialog', {dialog: 'account', val: 'login'});
            this.accountCallback = callback;
        },
        showModalAndSync: function(closeAfterDone = false, callback = null) {
            this.$store.commit('setShowDialog', {dialog: 'sync', val: true});
            const self = this;
            this.syncDatabase(function(error) {
                if (! error && closeAfterDone) {
                    // Close after some delay
                    if (self.$store.state.syncError) return; // don't close if there's an error

                    setTimeout(function() {
                        self.$store.commit('setShowDialog', {dialog: 'sync', val: false});
                    }, 500);
                }
                if (callback) callback(error);
            });
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
                            self.$store.commit('setSyncError', error);
                            self.$store.commit('setIsSyncing', false);
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
        syncDatabase: function(callback) {
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
                    self.$store.commit('setSyncError', error);
                    self.$store.commit('setIsSyncing', false);
                    callback(error);
                    return;
                }
                self.$store.commit('addSyncProgress', `Modified ${serverLastSyncDateString}`);
                const serverLastSyncDate = serverLastSyncDateString === null ? null : Date.parse(serverLastSyncDateString);
                if (serverLastSyncDate !== null && (serverLastSyncDate > lastSyncDate || lastSyncDate === null)) {
                    // Server version is newer, download, merge and upload
                    self.$store.commit('addSyncProgress', `Server version is newer (local = ${lastSyncDateString})`);
                    self.downloadDatabase(function(remoteData, error) {
                        if (error) {
                            self.$store.commit('setSyncError', error);
                            self.$store.commit('setIsSyncing', false);
                            return callback(error);
                        }
                        if (! self.$store.state.needSync) {
                            self.$store.commit('addSyncProgress', 'No new local data to merge');
                            self.$store.commit('setIsSyncing', false);
                            self.$store.commit('setLastSyncDate', serverLastSyncDateString);
                            return callback();
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

                            // For other (like options) take those with newest timestamp
                            const localOtherIdx = localData.data.tables.map((table) => table.name).indexOf('other');
                            const remoteOtherIdx = remoteData.data.tables.map((table) => table.name).indexOf('other');
                            const localOther = localData.data.data[localOtherIdx].rows;
                            const remoteOther = localData.data.data[remoteOtherIdx].rows;
                            const other = {};
                            localData.data.data[localOtherIdx].rows.forEach((row) => other[row.id] = row);
                            remoteData.data.data[remoteOtherIdx].rows.forEach((row) => {
                                if (other[row.id] && row.timestamp < other[row.id].timestamp) {
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

                            // Upload
                            importDatabaseJson(localData, self.$store, function(error) {
                                if (error) {
                                    self.$store.commit('setSyncError', error);
                                    self.$store.commit('setIsSyncing', false);
                                    return callback(error);
                                }

                                self.$store.commit('addSyncProgress', 'Uploading merged database');
                                const data = JSON.stringify(localData);
                                self.getLinkAndUploadData(data, function(error) {
                                    if (error) {
                                        self.$store.commit('setSyncError', error);
                                        self.$store.commit('setIsSyncing', false);
                                        return callback(error);
                                    }

                                    self.$store.commit('setIsSyncing', false);
                                    return callback();
                                });
                            });

                        });

                    });
                }
                else if (serverLastSyncDate !== null && serverLastSyncDate === lastSyncDate && ! self.$store.state.needSync) {
                    // The server version is the same as local, don't upload
                    self.$store.commit('addSyncProgress', 'Server version is is same as local data and no local changes, not uploading');
                    self.$store.commit('setIsSyncing', false);
                    return callback();
                }
                else {
                    // Server version is older or same as previously synced (or doesn't exist), 
                    // or we have new local changes, so just upload
                    self.$store.commit('addSyncProgress', `Server version is older (local=${lastSyncDateString}), uploading our local data`);
                    self.exportUploadDatabase(function(error) {
                        if (error) {
                            self.$store.commit('setSyncError', error);
                            self.$store.commit('setIsSyncing', false);
                            return callback(error);
                        }

                        self.$store.commit('setIsSyncing', false);
                        return callback();
                    });
                }
            });
        },
        setPlaying: function(showId, seasonIdx = 0, episodeIdx = 0) {
            if (this.showInfo.embeddable === false) {
                this.$store.commit('setNonEmbeddableVideoSelected', this.showInfo);
                this.$store.commit('setShowDialog', {dialog: 'embeddable', val: true});
                return;
            }
            this.$store.commit('setPlayingShowId', showId);
            this.$store.commit('setPlayingSeason', seasonIdx);
            this.$store.commit('setPlayingEpisode', episodeIdx);
            if (BROWSER_EXTENSION) {
                document.location = this.getVideoURL(seasonIdx, episodeIdx);
            }
            else {
                this.$store.commit('setPage', 'player');
            }
        },
        goExternal: function() {
            const showInfo = this.$store.state.nonEmbeddableVideoSelected;
            const captionId = showInfo.seasons[this.playingSeason || 0].episodes[this.playingEpisode || 0].id;
            const videoId = videoIdFromCaptionId(captionId);
            const site = siteFromCaptionId(captionId);
            const template = this.$store.state.STRINGS[site].urlTemplates.videoId;
            const url = template.replace('${id}', videoId);
            window.open(url, '_blank').focus();
            this.$store.commit('setNonEmbeddableVideoSelected', null);
            this.$store.commit('setPlayingSeason', null);
            this.$store.commit('setPlayingEpisode', null);
            this.$store.commit('setShowDialog', {dialog: 'embeddable', val: false});
        },
        getVideoURL: function(seasonIdx, episodeIdx) {
            const captionId = this.showInfo.seasons[seasonIdx].episodes[episodeIdx].id;
            const videoId = videoIdFromCaptionId(captionId);
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
            appendSessionLog(this.$store, data);
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
            return this.$store.state.STRINGS[getCurrentSite()][name];
        },
    },
    computed: {
        showInfo: function() {
            if (this.$store.state.showList === null || this.$store.state.playingShowId === null) return null;
            return this.$store.state.showList[this.$store.state.playingShowId];
        },
        season: {
            get: function() { return this.$store.state.playingSeason; },
            set: function(val) { this.$store.commit('setPlayingSeason', val); },
        },
        episode: {
            get: function() { return this.$store.state.playingEpisode; },
            set: function(val) { this.$store.commit('setPlayingEpisode', val); },
        },
        captionId: function() {
            if ([null, undefined].includes(this.showInfo)) return null;
            return this.showInfo.seasons[this.season].episodes[this.episode].id;
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
            if (this.$store.state.accessToken === null || personalFilter === null || showBloomFilters === null) return {};
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
        pinLevelStates: function() {
            return {
                py: this.getLvlStates('py', false, this.$store.state.options.pinLevels.py),
                hz: this.getLvlStates('hz', false, this.$store.state.options.pinLevels.hz),
                tr: this.getLvlStates('tr', false, this.$store.state.options.pinLevels.tr),
            }
        },
        videoWordStats: function() {
            if (this.$store.state.captionData === null) return {};
            const wordStats = {};
            for (let line of this.$store.state.captionData.lines) {
                line = captionArrayToDict(line, this.$store.state.captionData);
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
            const states = this.$store.state.peekStates;
            states['translation'] = states['translation'] && this.hiddenStates['translation'];
            for (var i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = states[type][i] && this.hiddenStates[type][i];
                }
            }
            return states;
        },
    },
};
