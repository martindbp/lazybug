try {
    importScripts('dexie.min.js');
} catch (e) {
    console.error(e);
}

db = new Dexie('zimuai');
db.version(1).stores({
    network: 'id',
    knowledge: 'id',
    other: 'id',
});

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
    return store.bulkGet(keys).then(function(data) {
        if (data) return data.map((item) => item ? item.value : null);
        return null;
    });
}

function updateStorageData(keys, values, store) {
    const entries = [];
    for (let i = 0; i < keys.length; i++) {
        console.log('Update storage', keys[i]);
        entries.push(store.update(keys[i], {value: values[i]}));
    }

    console.log('Update', entries);
    return Promise.all(entries);
}

function addStorageData(keys, values, store) {
    const entries = [];
    for (let i = 0; i < keys.length; i++) {
        entries.push({id: keys[i], value: values[i]});
    }

    console.log('Add', entries);
    return store.bulkAdd(entries);
}


const CDN_URL = "https://cdn.zimu.ai/file/";

function fetchVersionedResource(folder, resourceFilename, callback, failCallback) {
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

    const getStorageHashPromise = getStorageData([storageHashKey], db.network)
        .then((data) => data[0]);

    Promise.all([fetchHashPromise, getStorageHashPromise])
    .then(function(values) {
        const fetchHash = values[0].trim();
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
                        return updateStorageData(keys, values, db.network)
                            .then(() => data);
                    }
                    else {
                        return addStorageData(keys, values, db.network)
                            .then(() => data);
                    }
                });
        } else {
            return getStorageData([storageFileKey], db.network)
                .then((data) => data[0]);
        }
    })
    .then(function(data) {
        callback(data);
    }).catch((error) => {
        failCallback(error);
    });
}

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type === 'fetchVersionedResource') {
        fetchVersionedResource('zimu-public', message.filename, function (data) {
            sendResponse({data: data});
        }, function(error) {
            console.log('ERROR');
            console.log(error);
        });
    }
    else if (message.type === 'getCaptions') {
        fetchVersionedResource('zimu-public/subtitles', `${message.data.captionId}.json`, function (data) {
            sendResponse({data: data});
            chrome.runtime.sendMessage({type: 'requestSucceeded'});
        }, function(response) {
            chrome.runtime.sendMessage({type: 'requestFailed'});
            sendResponse('error');
        });
    }
    else if (message.type === 'getIndexedDbData') {
        const storage = db[message.storage];
        getStorageData(message.keys, storage)
            .then(function(data) {
                console.log(message.keys, 'got', data);
                sendResponse({data: data});
            })
            .catch((error) => sendResponse('error'));
    }
    else if (message.type === 'setIndexedDbData') {
        const storage = db[message.storage];
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

    return true;
});
