try {
    importScripts('vars_ext.js');
    BACKGROUND_SCRIPT = true; // set this so that shared.js doesn't try to create iframe
    importScripts('shared.js');
    importScripts('db.js');
} catch (e) {
    console.log(e);
}

let personalDb = initPersonalDb();
let cacheDb = initCacheDb();
let CACHE_HASHES_DURATION_S = 60*60;
if (LOCAL) {
    CACHE_HASHES_DURATION_S = 0;
}

const TRANSLATION_URL = 'http://localhost:8001';

function clearIndexedDb() {
    console.log('Clearing personal and cache IndexedDB');
    personalDb.delete();
    cacheDb.delete();
    personalDb = initPersonalDb();
    cacheDb = initCacheDb();
}

function backgroundClearCache() {
    console.log('Clearing IndexedDB cache');
    cacheDb.network.clear();
}

function backgroundClearPersonalData() {
    console.log('Clearing personal data in IndexedDB');
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

function upgradeDatabase(data, callback) {
    // Takes a database in JSON format, e.g. downloaded from remote and applies upgrades to it if any are available
    const TMP_NAME = 'lazybug-tmp';
    let tmpDatabase = new Dexie(TMP_NAME);
    tmpDatabase.delete(); // delte any old data if there
    tmpDatabase = initPersonalDb(data.data.databaseVersion, TMP_NAME); // only apply up to version in data
    // Change the name of the database in the data (have to do this, or we can't import it into lazybug-tmp
    data.data.databaseName = TMP_NAME;

    const str = JSON.stringify(data);
    const bytes = new TextEncoder().encode(str);
    const blob = new Blob([bytes], {
        type: "application/json;charset=utf-8"
    });

    DexieExportImport.peakImportFile(blob).then(function(fileMeta) {
        tmpDatabase.import(blob, { overwriteValues: true })
        .then(() => {
            return tmpDatabase.close();
        })
        .then(() => {
            // Apply all versions
            applyDbVersions(tmpDatabase, PERSONAL_DB_VERSIONS);
        })
        .then(() => {
            return tmpDatabase.open();
        })
        .then(() => {
            tmpDatabase.export({ prettyJson: true }).then(function(data) {
                const fr = new FileReader();
                fr.addEventListener("load", e => {
                    let upgradedData = JSON.parse(fr.result);
                    // Change back the database name from lazybug-tmp to lazybug-personal
                    upgradedData.data.databaseName = 'lazybug-personal';
                    callback(upgradedData);
                });
                fr.readAsText(data);
                tmpDatabase.delete()
            });
        })
        .catch((error) => {
            callback(null, error);
        });
    })
}

function backgroundImportDatabaseJson(data, callback) {
    const str = JSON.stringify(data);
    const bytes = new TextEncoder().encode(str);
    const blob = new Blob([bytes], {
        type: "application/json;charset=utf-8"
    });

    DexieExportImport.peakImportFile(blob).then(function(fileMeta) {
        const version = fileMeta.data.databaseVersion;

        // Deleting curent
        console.log('Deleting personal data before importing');
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
            const ms = Date.now();
            return fetch(CDN_URL + `${folder}/${filename}.hash?dummy=${ms}`, {cache: 'no-cache'})
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
                    return fetch(CDN_URL + `${folder}/${filename}-${fetchHash}.${ext}`, {cache: 'no-cache'})
                        .then(function(response) {
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
    if (message.type === 'ping') {
        sendResponse({data: 'pong'});
    }
    else if (message.type === 'clearCache') {
        backgroundClearCache();
        sendResponse();
    }
    else if (message.type === 'clearPersonalData') {
        backgroundClearPersonalData();
        sendResponse();
    }
    else if (message.type === 'fetchVersionedResource') {
        backgroundFetchVersionedResource('lazybug-public', message.filename, function (data, hash) {
            clearNetworkError();
            sendResponse({data: data, hash: hash});
        }, function(error) {
            setNetworkError();
            sendResponse('error');
        });
    }
    else if (message.type === 'fetchResource') {
        backgroundFetchResource('lazybug-public', message.filename, function (data) {
            sendResponse({data: data});
            clearNetworkError();
        }, function(error) {
            setNetworkError();
            sendResponse('error');
        });
    }
    else if (message.type === 'getCaptions') {
        backgroundFetchVersionedResource('lazybug-public/subtitles', `${message.data.captionId}.json`, function (data, hash) {
            clearNetworkError();
            sendResponse({data: {data: data, hash: hash}});
        }, function(response) {
            setNetworkError();
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
                console.log('setIndexedDbData error', error);
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
                    console.log('appendSessionLog error', error);
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
                    console.log('appendSessionLog error', error);
                    sendResponse('error');
                });
            }
        });
    }
    else if (message.type === 'poll') {
        console.log('Polling');
        fetch(TRANSLATION_URL).then(function(response) {
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
    else if (message.type === 'isPersonalDbEmpty') {
        personalDb.log.count().then(function(count) {
            sendResponse({data: count === 0});
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
    else if (message.type === 'getViewingHistory') {
        // message parameters:
        // offset
        // limit
        // dedupeGobal: AABAAB -> AB
        // dedupeLast: AABAAB -> ABAB

        let seen = new Set();
        let lastCaptionId = null;
        message.offset = message.offset || 0;

        personalDb.log
        .reverse()
        .sortBy('sessionTime')
        .then(function(data) {
            let videos = [];
            for (const session of data) {
                if (message.dedupeGlobal && seen.has(session.captionId)) continue;
                if (message.dedupeLast && session.captionId === lastCaptionId) continue;
                if ([null, undefined].includes(session.showId)) continue;

                videos.push({
                    captionId: session.captionId,
                    showId: session.showId,
                    seasonIdx: session.seasonIdx,
                    episodeIdx: session.episodeIdx,
                });

                seen.add(session.captionId);
                lastCaptionId = session.captionId;
                if (
                    message.limit &&
                    videos.length > message.offset + message.limit
                ) break;
            }
            videos = videos.slice(message.offset);
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
    else if (message.type === 'getLastViewingPosition') {
        personalDb.log
        .where('captionId')
        .equals(message.captionId)
        .reverse()
        .sortBy('sessionTime')
        .then(function(data) {
            let maxIdx = -1;
            for (const row of data) {
                for (let i = 0; i < row.eventIds.length; i++) {
                    if (row.eventIds[i] === events.indexOf('EVENT_SHOW_CAPTION_IDX')) {
                        maxIdx = Math.max(maxIdx, row.eventData[i][0]);
                    }
                }
            }
            sendResponse({data: maxIdx});
        })
        .catch(function(error) {
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'getAnswerHistory') {
        personalDb.log
        .where('eventIds')
        .between(events.indexOf('EVENT_ANSWER_PY'), events.indexOf('EVENT_ANSWER_TR') + 1)
        .and(item => ! item.isReview)
        .reverse()
        .sortBy('sessionTime')
        .then(function(data) {
            sendResponse({data: data});
        })
        .catch(function(error) {
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'getLoginCredentials') {
        if (getCookie('jwt')) {
            sendResponse({data: {email: getCookie('email'), accessToken: getCookie('jwt')}});
        }
        else {
            sendResponse(null);
        }
        return true;
    }
    else if (message.type === 'getDiscourseTopicComments') {
        if (LOCAL) {
            // Return fake data
            let showId = message.showId;
            let season = message.season + 1;
            let episode = message.episode + 1;
            let posts = [{ // first post is system
                post_number: 0,
                username: "system",
                cooked: `\u003cp\u003e\u003ca href=\"https://lazybug.ai/player/${showId}/${season}/${episode}\"\u003eLink\u003c/a\u003e\u003c/p\u003e`,
                reply_to_post_number: null,
                created_at:"2022-09-24T12:03:01.473Z",
                link_counts: [
                   {
                      url: `https://lazybug.ai/player/${showId}/${season}/${episode}`,
                   }
                ],
            }]
            for (let i = 0; i < 10; i++) {
                if (i % 2 == 1) continue; // leave every other caption empty
                // Create one caption comment and one response to it
                posts.push({
                    post_number: 1 + 2*i,
                    username: "user1",
                    cooked:`\u003cblockquote\u003e\n\u003cp\u003e\u003ca href=\"https://lazybug.ai/${showId}/${season}/${episode}/${i+1}\"\u003eS01E01 - 00:30:22\u003c/a\u003e\u003cbr\u003e\n你 好像 不 爱 吃 馒头 啊\u003cbr\u003e\nnǐ hǎoxiàng bù ài chī mántou a\u003cbr\u003e\nYou don’t seem to like steamed buns.\u003c/p\u003e\n\u003c/blockquote\u003e\n\u003cp\u003etest\u003c/p\u003e`,
                    reply_to_post_number: null,
                    created_at:"2022-09-24T12:03:01.473Z",
                    link_counts: [
                       {
                          url: `https://lazybug.ai/player/${showId}/${season}/${episode}/${i+1}`,
                       }
                    ],
                });
                posts.push({
                    post_number: 1 + 2*i + 1,
                    username: "user2",
                    cooked: `\u003cblockquote\u003e\u003cblockquote\u003e\n\u003cp\u003e\u003ca href=\"https://lazybug.ai/${showId}/${season}/${episode}/${i+1}\"\u003eS01E01 - 00:30:22\u003c/a\u003e\u003cbr\u003e\n你 好像 不 爱 吃 馒头 啊\u003cbr\u003e\nnǐ hǎoxiàng bù ài chī mántou a\u003cbr\u003e\nYou don’t seem to like steamed buns.\u003c/p\u003e\n\u003c/blockquote\u003e\n\u003cp\u003etest\u003c/p\u003e\u003c/blockquote\u003e\n\u003cp\u003eOK\u003c/p\u003e`,
                    reply_to_post_number: 2*i,
                    created_at:"2022-09-24T12:03:01.473Z",
                    link_counts: [
                       {
                          url: `https://lazybug.ai/player/${showId}/${season}/${episode}/${i+1}`,
                       }
                    ],
                });
            }

            sendResponse({data: posts});
            return true;
        }

        // NOTE: by default this endpoint returns only 20 comments, it's reported that with `print=true` it
        // should return 1000.
        const topicURL = `${DISCOURSE_COMMENTS_URL}/${message.data}.json?print=true`;
        fetch(topicURL, {
            method: 'GET',
            credentials: 'include',
        }).then((response) => {
            if (!response.ok) {
                throw new Error('Fetch failed');
            }
            return response;
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.post_stream && data.post_stream.posts) {
                if (data.post_stream.posts.length === 1000) {
                    console.log(`{topicURL} returned 1000 comments, may have reached limit of API`);
                }
                sendResponse({data: data.post_stream.posts})
            }
            else {
                sendResponse('error');
            }
        })
        .catch(function(error) {
            console.log(error);
            sendResponse('error');
        });
    }
    else if (message.type === 'translation') {
        fetch(TRANSLATION_URL, { method: 'POST', body: message.data }).then(() => sendResponse());
    }

    return true;
}

let extensionOn = null;

function updateExtensionStatusBadge() {
    if (extensionOn) {
        chrome.action.setBadgeText({ text: "" });
        chrome.action.setBadgeBackgroundColor({ color: "rgba(0,0,0,0)" });
    }
    else {
        chrome.action.setBadgeText({ text: "OFF" });
        chrome.action.setBadgeBackgroundColor({ color: "red" });
    }
}

function setNetworkError() {
    if (! BROWSER_EXTENSION) return;
    chrome.action.setBadgeText({ text: "ERR" });
    chrome.action.setBadgeBackgroundColor({ color: "red" });
}

function clearNetworkError() {
    if (! BROWSER_EXTENSION) return;
    updateExtensionStatusBadge();
}

if (BROWSER_EXTENSION) {
    //
    // NOTE: background.js is only used from browser extension for deepl and extension toggling
    //

    chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
        backgroundMessageHandler(message, null, function(response) {
            sendResponse(response);
            return true;
        });
        return true;
    });

    function toggleExtension() {
        extensionOn = ! extensionOn;
        chrome.storage.local.set({"extensionOn": extensionOn}, function() {});
        updateExtensionStatusBadge();
        chrome.tabs.query({}, function(tabs) {
            for (const tab of tabs) {
                chrome.tabs.sendMessage(tab.id, {type: "extensionOn", data: extensionOn});
            }
        });
    }

    chrome.storage.local.get("extensionOn", function(data) {
        // Set opposite value and toggle to update badge and send message to content script
        console.log('extensionOn=', data.extensionOn);
        extensionOn = ! data.extensionOn;
        toggleExtension();
    });

    chrome.action.onClicked.addListener(toggleExtension);
}
else {
    if (window.parent != window) {
        // We're inside an iframe, listen to messages from the parent
        window.addEventListener("message", message => {
            backgroundMessageHandler(message.data.message, null, function(response) {
                window.parent.postMessage({
                    data: response,
                    requestId: message.data.requestId,
                }, '*');
            });
        });
    }
}
