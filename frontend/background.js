try {
    importScripts('vars_ext.js');
    importScripts('shared.js');
    importScripts('db.js');
} catch (e) {
    console.log(e);
}

let personalDb = initPersonalDb();
let cacheDb = initCacheDb();
const CACHE_HASHES_DURATION_S = 60*60;

function clearIndexedDb() {
    personalDb.delete();
    cacheDb.delete();
    personalDb = initPersonalDb();
    cacheDb = initCacheDb();
}

function backgroundClearCache() {
    cacheDb.network.clear();
}

function backgroundClearPersonalData() {
    personalDb.delete();
    personalDb = initPersonalDb();
}

function backgroundExportDatabaseJson(callback) {
    personalDb.export({ prettyJson: true }).then(function(data) {
        const fr = new FileReader();
        fr.addEventListener("load", e => {
            callback(JSON.parse(fr.result));
        });
        fr.readAsText(data);
    });
}

function backgroundImportDatabaseJson(data, callback) {
    const str = JSON.stringify(data);
    const bytes = new TextEncoder().encode(str);
    const blob = new Blob([bytes], {
        type: "application/json;charset=utf-8"
    });

    // Deleting curent
    personalDb.delete();
    personalDb = initPersonalDb();
    DexieExportImport.peakImportFile(blob).then(function(fileMeta) {
        const version = fileMeta.data.databaseVersion;

        personalDb.delete();
        personalDb = initPersonalDb(version);

        personalDb.import(blob, { overwriteValues: true })
        .then(() => {
            return personalDb.close();
        })
        .then(() => {
            applyDbVersions(personalDb, PERSONAL_DB_VERSIONS, version);
        })
        .then(() => {
            return personalDb.open();
        })
        .then(() => {
            callback();
        })
        .catch((error) => {
            callback(error);
        });
    });
}

function showBadgeStatus() {
    chrome.action.setBadgeBackgroundColor({color:[0, 150, 0, 255]});
    chrome.action.setBadgeText({text:'✓'});
}

function clearBadgeStatus() {
    chrome.action.setBadgeText({text:''})
}

function getStorageData(keys, store) {
    if (keys === null) {
        return store.toArray().then();
    }
    console.log('Get storage', keys);
    return store.bulkGet(keys)
        .then(function(data) {
            if (data) return data;
            return null;
        });
}

function updateStorageData(keys, values, store) {
    const entries = [];
    for (let i = 0; i < keys.length; i++) {
        console.log('Update storage', keys[i]);
        entries.push(store.update(keys[i], {value: values[i], timestamp: Date.now()}));
    }

    return Promise.all(entries);
}

function addStorageData(keys, values, store) {
    const entries = [];
    for (let i = 0; i < keys.length; i++) {
        entries.push({id: keys[i], value: values[i], timestamp: Date.now()});
    }

    console.log('Add', entries);
    return store.bulkAdd(entries);
}


function backgroundFetchResource(folder, resourceFilename, callback, failCallback) {
    console.log(folder, resourceFilename);
    let [filename, ext] = resourceFilename.split('.');
    const storageFilename = `${folder}/${filename}.${ext}`;

    getStorageData([storageFilename], cacheDb.network)
    .then(function(data) {
        if ([null, undefined].includes(data[0])) {
            return fetch(CDN_URL + storageFilename, {cache: 'default'})
                .then(function(response) {
                    if (!response.ok) {
                        failCallback(response);
                        return null;
                    }
                    return response;
                })
                .then((response) => response.json())
                .then(function(data) {
                    console.log('Fetching done for', folder, filename);

                    const keys = [storageFilename];
                    const values = [data];
                    return addStorageData(keys, values, cacheDb.network)
                        .then(() => data);
                });
        }
        else {
            return data[0].value;
        }
    })
    .then(function(data) {
        callback(data);
    });
}


function backgroundFetchVersionedResource(folder, resourceFilename, callback, failCallback) {
    console.log(folder, resourceFilename);
    let [filename, ext] = resourceFilename.split('.');
    
    const storageHashKey = `${folder}/${filename}.hash`;
    const storageFileKey = `${folder}/${filename}.${ext}`;

    // NOTE: never cache the hash files, we purge those manually from Cloudflare
    console.log('Fetching hash for ', `${folder}/${filename}.hash`);

    let hash = null;

    getStorageData([storageHashKey], cacheDb.network)
    .then(function(data) {
        const storageHash = data && data[0] !== undefined ? data[0].value : null;
        hash = storageHash;
        const secondsSinceUpdated = storageHash ? (Date.now() - data[0].timestamp) / 1000 : null;
        if (secondsSinceUpdated !== null & secondsSinceUpdated < CACHE_HASHES_DURATION_S) {
            console.log(folder, 'hash file cache timestamp within duration');
            return getStorageData([storageFileKey], cacheDb.network)
                   .then((data) => data[0].value);
        }
        else {
            console.log(folder, 'hash file cache timestamp is stale');
            return fetch(CDN_URL + `${folder}/${filename}.hash`, {cache: 'no-cache'})
            .then(function(response) {
                console.log('Fetching done for ', folder);
                if (!response.ok) {
                    failCallback(response);
                    return null;
                }
                return response;
            })
            .then(response => response.text())
            .then((fetchHash) => {
                fetchHash = fetchHash.trim();
                hash = fetchHash;
                if (fetchHash !== storageHash) {
                    console.log('Fetching', folder, filename, fetchHash);
                    return fetch(CDN_URL + `${folder}/${filename}-${fetchHash}.${ext}`, {cache: 'default'})
                        .then(function(response) {
                            if (BROWSER_EXTENSION) {
                                chrome.action.setBadgeText({text:''});
                            }
                            if (!response.ok) {
                                failCallback(response);
                                return null;
                            }
                            return response;
                        })
                        .then((response) => response.json())
                        .then(function(data) {
                            console.log('Fetching done for', folder, filename, fetchHash);

                            const keys = [storageFileKey, storageHashKey];
                            const values = [data, fetchHash];
                            if (storageHash) {
                                return updateStorageData(keys, values, cacheDb.network)
                                    .then(() => data);
                            }
                            else {
                                return addStorageData(keys, values, cacheDb.network)
                                    .then(() => data)
                                    .catch((error) => {
                                        // BulkError, probably requested same resource twice
                                        return data;
                                    });
                            }
                        });
                } else {
                    // Need to update the timestamp for the hash file
                    const keys = [storageHashKey];
                    const values = [fetchHash];
                    return updateStorageData(keys, values, cacheDb.network)
                        .then(() => {
                            return getStorageData([storageFileKey], cacheDb.network)
                               .then((data) => data[0].value);
                        });
                }
            })
        }
    })
    .then(function(data) {
        callback(data, hash);
    }).catch((error) => {
        failCallback(error);
    });
}

function backgroundMessageHandler(message, sender, sendResponse) {
    if (message.type === 'clearCache') {
        backgroundClearCache();
        sendResponse();
    }
    else if (message.type === 'clearPersonalData') {
        backgroundClearPersonalData();
        sendResponse();
    }
    else if (message.type === 'fetchVersionedResource') {
        backgroundFetchVersionedResource('zimu-public', message.filename, function (data, hash) {
            sendResponse({data: data, hash: hash});
        }, function(error) {
            console.log('ERROR');
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'fetchResource') {
        backgroundFetchResource('zimu-public', message.filename, function (data) {
            sendResponse({data: data});
        }, function(error) {
            console.log('ERROR');
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'getCaptions') {
        backgroundFetchVersionedResource('zimu-public/subtitles', `${message.data.captionId}.json`, function (data, hash) {
            sendResponse({data: data, hash: hash});
        }, function(response) {
            sendResponse('error');
        });
    }
    else if (message.type === 'getIndexedDbData') {
        const storage = personalDb[message.storage];
        getStorageData(message.keys, storage)
        .then(function(data) {
            console.log(message.keys, 'got', data);
            if (message.keys !== null) {
                const values = data.map((item) => item.value);
                sendResponse({data: values});
            }
            else {
                sendResponse({data: data});
            }
        })
        .catch((error) => sendResponse('error'));
    }
    else if (message.type === 'setIndexedDbData') {
        const storage = personalDb[message.storage];
        const data = {};
        let keys = message.keys;
        let values = message.values;
        if (message.keys === null) {
            // No keys set means that keys and values are in message.values
            keys = Object.keys(message.values);
            values = keys.map((key) => message.values[key]);
        }
        addStorageData(keys, values, storage)
        .then(function() {
            sendResponse();
        })
        .catch(function(error) {
            console.log("Adding didn't work, trying updating instead");
            // Adding didn't work, try updating
            return updateStorageData(keys, values, storage)
            .then(function() {
                sendResponse();
            })
            .catch(function(error) {
                console.log(error);
                sendResponse('error');
            });
        });
    }
    else if (message.type === 'appendSessionLog') {
        const whereQuery = {
            captionId: message.sessionData.captionId,
            captionHash: message.sessionData.captionHash,
            sessionTime: message.sessionData.sessionTime,
        };
        personalDb.log.where(whereQuery).count(function(count) {
            if (count === 0) {
                message.sessionData.eventIds = [message.data[0]];
                message.sessionData.eventData = [message.data.slice(1)];
                message.sessionData.synced = false;
                personalDb.log.put(message.sessionData)
                .then(function() {
                    sendResponse();
                })
                .catch(function(error) {
                    console.log(error);
                    sendResponse('error');
                });
            }
            else {
                personalDb.log.where(whereQuery).modify(function(x) {
                    x.eventIds.push(message.data[0]);
                    x.eventData.push(message.data.slice(1));
                    x.synced = false;
                    // The names can be null the first time you load a page, so always update these
                    x.showName = message.sessionData.showName;
                    x.seasonName = message.sessionData.seasonName;
                    x.episodeName = message.sessionData.episodeName;
                })
                .then(function() {
                    sendResponse();
                })
                .catch(function(error) {
                    console.log(error);
                    sendResponse('error');
                });
            }
        });
    }
    else if (message.type === 'poll') {
        console.log('Polling');
        fetch('http://localhost:8000').then(function(response) {
            if (!response.ok) {
                console.log('No server running');
                sendResponse();
                return null;
            }
            return response;
        })
        .then(response => response.text())
        .then(data => sendResponse({'data': data}))
        .catch((error) => {
            console.log('No server running');
            sendResponse();
            return null;
        });
    }
    else if (message.type === 'getLog') {
        // NOTE: this paging filters using index in DB, but sorts in memory, see https://dexie.org/docs/Collection/Collection.offset()#a-better-paging-approach for potential fix
        personalDb.log
        .where('eventIds').between(events.indexOf('EVENT_STAR_CAPTION'), events.indexOf('EVENT_STAR_TRANSLATION') + 1)
        .reverse()
        .sortBy('sessionTime')
        .then(function(data) {
            sendResponse({data: data.slice(message.offset, message.offset+message.limit+1)});
        })
        .catch(function(error) {
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'getRecent') {
        let seen = new Set();

        personalDb.log
        .reverse()
        .sortBy('sessionTime')
        .then(function(data) {
            const videos = [];
            for (const session of data) {
                if (seen.has(session.captionId)) continue;
                if (session.showName === null) continue;

                videos.push({
                    captionId: session.captionId,
                    showName: session.showName,
                    seasonName: session.seasonName,
                    episodeName: session.episodeName
                });

                seen.add(session.captionId);
                if (videos.length > 10) break;
            }
            sendResponse({data: videos});
        })
        .catch(function(error) {
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'exportDatabaseJson') {
        backgroundExportDatabaseJson(function (data) {
            sendResponse({data: data});
        });
    }
    else if (message.type === 'importDatabaseJson') {
        backgroundImportDatabaseJson(message.data, function (message) {
            if (message !== undefined) message = String(message);
            sendResponse(message);
        });
    }
    else if (message.type === 'getLogRows') {
        personalDb.log
        .where('eventIds').between(events.indexOf('EVENT_STAR_CAPTION'), events.indexOf('EVENT_STAR_TRANSLATION') + 1)
        .count()
        .then(function(data) {
            sendResponse({data: data});
        });
    }
    else if (message.type === 'translation') {
        fetch('http://localhost:8000', { method: 'POST', body: message.data }).then(() => sendResponse());
    }
    else if (message.type === 'openDashboard') {
        if (BROWSER_EXTENSION) {
            chrome.tabs.create({
              url: "dashboard.html",
            });
        }
    }

    return true;
}

if (BROWSER_EXTENSION) {
    chrome.runtime.onMessage.addListener(backgroundMessageHandler);
}
