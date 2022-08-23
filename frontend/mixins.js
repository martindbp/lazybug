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
    methods: {
        showModalAndSync: function(closeAfterDone = false) {
            this.$store.commit('setShowSyncDialog', true);
            const self = this;
            this.syncDatabase(function(error) {
                if (! error && closeAfterDone) {
                    self.$store.commit('setShowSyncDialog', false);
                }
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
            self.$store.commit('addSyncProgress', 'Getting signed upload link');
            getSignedUploadLink(this.$store.state.accessToken, data.length, function(url, error) {
                if (error) {
                    callback(error);
                    return;
                }

                self.$store.commit('addSyncProgress', 'Uploading data');
                const date = (new Date()).toUTCString();
                self.$store.commit('setLastSyncDate', date);

                uploadData(url, data, date, function(error) {
                    if (error) {
                        callback(error);
                        return;
                    }

                    self.$store.commit('addSyncProgress', 'Successfully uploaded');
                    callback(); // success
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
            let lastSyncDate = this.$store.state.lastSyncDate;
            if (lastSyncDate !== null) lastSyncDate = Date.parse(lastSyncDate);
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
                const serverLastSyncDate = Date.parse(serverLastSyncDateString);
                if (serverLastSyncDate > lastSyncDate || (serverLastSyncDate !== null && lastSyncDate === null)) {
                    // Server version is newer, download, merge and upload
                    self.$store.commit('addSyncProgress', 'Server version is newer');
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
                            return;
                        }

                        // Get local database json
                        self.$store.commit('addSyncProgress', 'Local database has new data, exporting');
                        exportDatabaseJson(function(localData) {
                            // Merge
                            self.$store.commit('addSyncProgress', 'Merging local and remote database');

                            self.$store.commit('addSyncProgress', 'Uploading merged database');

                            // Upload
                            const data = JSON.stringify(localData);
                            self.getLinkAndUploadData(data, function(error) {
                                if (error) {
                                    self.$store.commit('setSyncError', error);
                                    self.$store.commit('setIsSyncing', false);
                                    return callback(error);
                                }

                                self.$store.commit('setIsSyncing', false);
                            });
                        });

                    });
                }
                else if (serverLastSyncDate === lastSyncDate && ! self.$store.state.needSync) {
                    // The server version is the same as local, don't upload
                    self.$store.commit('addSyncProgress', 'Server version is is same as local data and no local changes, not uploading');
                    self.$store.commit('setIsSyncing', false);
                }
                else {
                    // Server version is older or same as previously synced (or doesn't exist), 
                    // or we have new local changes, so just upload
                    self.$store.commit('addSyncProgress', 'Server version is older, uploading our local data');
                    self.exportUploadDatabase(function(error) {
                        if (error) {
                            self.$store.commit('setSyncError', error);
                            self.$store.commit('setIsSyncing', false);
                            return callback(error);
                        }

                        self.$store.commit('setIsSyncing', false);
                    });
                }
            });
        },
        setPlaying: function(showInfo, seasonIdx = 0, episodeIdx = 0) {
            if (showInfo.embeddable === false) {
                this.$store.commit('setNonEmbeddableVideoSelected', showInfo);
                this.$store.commit('setShowNonEmbeddableDialog', true);
                return;
            }
            this.$store.commit('setPlayingShowInfo', showInfo);
            this.$store.commit('setPlayingSeason', seasonIdx);
            this.$store.commit('setPlayingEpisode', episodeIdx);
            this.$store.commit('setWebPage', 'player');
        },
        goYoutube: function() {
            const showInfo = this.$store.state.nonEmbeddableVideoSelected;
            const captionId = showInfo.seasons[this.playingSeason].episodes[this.playingEpisode].id;
            const parts = captionId.split('-');
            const id = parts.slice(1).join('-');
            const list = showInfo.seasons[0].youtube_playlist;
            let url = `https://youtube.com/watch?v=${id}`;
            if (list) {
                url += `&list=${list}`;
            }
            window.open(url, '_blank').focus();
            this.$store.commit('setNonEmbeddableVideoSelected', null);
            this.$store.commit('setPlayingSeason', null);
            this.$store.commit('setPlayingEpisode', null);
            this.$store.commit('setShowNonEmbeddableDialog', false);
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
    },
    computed: {
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
