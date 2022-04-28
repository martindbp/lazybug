try {
    importScripts('shared.js');
    importScripts('db.js');
} catch (e) {
    console.error(e);
}

let personalDb = initPersonalDb();
let cacheDb = initCacheDb();

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

    personalDb.import(blob, { overwriteValues: true })
    .then(() => {
        callback();
    })
    .catch((error) => {
        callback(error);
    });;
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
            if (data) return data.map((item) => item ? item.value : null);
            return null;
        });
}

function updateStorageData(keys, values, store) {
    const entries = [];
    for (let i = 0; i < keys.length; i++) {
        console.log('Update storage', keys[i]);
        entries.push(store.update(keys[i], {value: values[i], timestamp: Date.now()}));
    }

    console.log('Update', entries);
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


const CDN_URL = "https://cdn.zimu.ai/file/";
function backgroundFetchResource(folder, resourceFilename, callback, failCallback) {
    console.log(folder, resourceFilename);
    let [filename, ext] = resourceFilename.split('.');
    const storageFilename = `${folder}/${filename}.${ext}`;

    getStorageData([storageFilename], cacheDb.network)
    .then(function(data) {
        if (data[0] === null) {
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
            return data[0];
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
    const fetchHashPromise = fetch(CDN_URL + `${folder}/${filename}.hash`, {cache: 'no-cache'})
    .then(function(response) {
        console.log('Fetching done for ', folder);
        if (!response.ok) {
            failCallback(response);
            return null;
        }
        return response;
    })
    .then(response => response.text());

    const getStorageHashPromise = getStorageData([storageHashKey], cacheDb.network)
        .then((data) => data[0]);

    let fetchHash = null;
    Promise.all([fetchHashPromise, getStorageHashPromise])
    .then(function(values) {
        fetchHash = values[0].trim();
        const storageHash = values[1];
        console.log('Got hashes', fetchHash, storageHash);
        if (fetchHash !== storageHash) {
            console.log('Fetching', folder, filename, fetchHash);
            return fetch(CDN_URL + `${folder}/${filename}-${fetchHash}.${ext}`, {cache: 'default'})
                .then(function(response) {
                    chrome.action.setBadgeText({text:''});
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
                    if (storageHashKey) {
                        return updateStorageData(keys, values, cacheDb.network)
                            .then(() => data);
                    }
                    else {
                        return addStorageData(keys, values, cacheDb.network)
                            .then(() => data);
                    }
                });
        } else {
            return getStorageData([storageFileKey], cacheDb.network)
                   .then((data) => data[0]);
        }
    })
    .then(function(data) {
        callback(data, fetchHash);
    }).catch((error) => {
        failCallback(error);
    });
}

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
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
            chrome.runtime.sendMessage({type: 'requestSucceeded'});
        }, function(response) {
            chrome.runtime.sendMessage({type: 'requestFailed'});
            sendResponse('error');
        });
    }
    else if (message.type === 'getIndexedDbData') {
        const storage = personalDb[message.storage];
        getStorageData(message.keys, storage)
        .then(function(data) {
            console.log(message.keys, 'got', data);
            sendResponse({data: data});
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
        const whereQuery = {captionId: message.captionId, captionHash: message.captionHash, sessionTime: message.sessionTime};
        personalDb.log.where(whereQuery).count(function(count) {
            if (count === 0) {
                whereQuery.eventIds = [message.data[0]];
                whereQuery.eventData = [message.data.slice(1)];
                personalDb.log.put(whereQuery)
                .then(function() {
                    sendResponse(null);
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
                })
                .then(function() {
                    sendResponse();
                })
                .catch(function(error) {
                    console.log(error);
                    sendResponse('error');
                });
            }
        })
    }
    else if (message.type === 'poll') {
        console.log('Polling');
        fetch('http://localhost:8000').then(function(response) {
            if (!response.ok) {
                console.log('No server running');
                sendResponse(null);
                return null;
            }
            return response;
        })
        .then(response => response.text())
        .then(data => sendResponse({'data': data}))
        .catch((error) => {
            console.log('No server running');
            sendResponse(null);
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
            sendResponse({data: data.slice(message.offset, message.offset+message.limit)});
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
        fetch('http://localhost:8000', { method: 'POST', body: message.data }).then(() => sendResponse(null));
    }
    else if (message.type === 'openDashboard') {
        chrome.tabs.create({
          url: "dashboard.html",
        });
    }

    return true;
});
