function showBadgeStatus() {
    chrome.action.setBadgeBackgroundColor({color:[0, 150, 0, 255]});
    chrome.action.setBadgeText({text:'✓'});
}

function clearBadgeStatus() {
    chrome.action.setBadgeText({text:''})
}

function getStorageData(key) {
    console.log('Get storage', key);
    return new Promise((resolve, reject) => {
        chrome.storage.local.get([key], (items) => {
            console.log('Done', key);
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError);
            }
            resolve(items[key]);
        });
    });
}

function setStorageData(data) {
    return new Promise((resolve, reject) => {
        chrome.storage.local.set(data, function() {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError);
            }
            resolve();
        });
    });
}

const CDN_URL = "https://cdn.zimu.ai/file/";

function fetchVersionedResource(folder, resourceFilename, callback, failCallback) {
    console.log(folder, resourceFilename);
    let [filename, ext] = resourceFilename.split('.');
    
    const storageHashKey = `${folder}/${filename}.hash`;
    const storageFileKey = `${folder}/${filename}.${ext}`;

    // NOTE: never cache the hash files, we purge those manually from Cloudflare
    console.log('Fetching hash for ', folder);
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

    const getStorageHashPromise = getStorageData(storageHashKey);

    Promise.all([fetchHashPromise, getStorageHashPromise])
    .then(function(values) {
        const fetchHash = values[0].trim();
        const storageHash = values[1];
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

                    const storeData = {};
                    storeData[storageFileKey] = data;
                    storeData[storageHashKey] = fetchHash;
                    return setStorageData(storeData)
                        .then(() => data);
                });
        } else {
            return getStorageData(storageFileKey);
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
            sendResponse({'data': data});
        }, function(error) {
            console.log('ERROR');
            console.log(error);
        });
    }
    else if (message.type == 'getCaptions') {
        fetchVersionedResource('zimu-public/subtitles', `${message.data.captionId}.json`, function (data) {
            sendResponse({'data': data});
            chrome.runtime.sendMessage({'type': 'requestSucceeded'});
        }, function(response) {
            chrome.runtime.sendMessage({'type': 'requestFailed'});
            sendResponse('error');
        });
    }

    return true;
});

let defaultOptions = {
};


// Set any missing option values to default value (for first time starting the extension)
// Can't do this from the options page, since it will probably not be opened before content/background
chrome.storage.sync.get('options', function(result) {
    if (result.options === undefined) {
        result.options = {};
    }
    for (let key of Object.keys(defaultOptions)) {
        if (! (key in result.options)) {
            result.options[key] = defaultOptions[key];
        }
    }

    chrome.storage.sync.set({
        options: result.options
    }, function() {});
});
