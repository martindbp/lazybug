function showBadgeStatus() {
    chrome.action.setBadgeBackgroundColor({color:[0, 150, 0, 255]});
    chrome.action.setBadgeText({text:'✓'});
}

function clearBadgeStatus() {
    chrome.action.setBadgeText({text:''})
}


const CDN_URL = "https://cdn.zimu.ai/file/";

function fetchVersionedResource(folder, resourceFilename, callback, failCallback) {
    let [filename, ext] = resourceFilename.split('.');
    
    // NOTE: never cache the hash files, we purge those manually from Cloudflare
    fetch(CDN_URL + `${folder}/${filename}.hash`, {cache: 'no-cache'})
    .then(function(response) {
        if (!response.ok) {
            failCallback(response);
            return null;
        }
        return response;
    })
    .then(response => response.text())
    .then(function(hash) {
        return fetch(CDN_URL + `${folder}/${filename}-${hash}.${ext}`, {cache: 'default'})
    })
    .then(function(response) {
        if (!response.ok) {
            failCallback(response);
            return null;
        }
        return response;
    })
    .then(response => response.json())
    .then(function(data) {
        callback(data);
    }).catch((error) => {
        failCallback(error);
    });
}

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type === 'contentOpened') {
        clearBadgeStatus();
    }

    if (message.type === 'fetchVersionedResource') {
        fetchVersionedResource('zimu-public', message.filename, function (data) {
            sendResponse({'data': data});
        }, function(error) {
            // do nothing
        });
    }
    else if (message.type == 'getCaptions') {
        clearBadgeStatus();
        fetchVersionedResource('zimu-public/subtitles', `${message.data.captionId}.json`, function (data) {
            showBadgeStatus();
            sendResponse({'data': data});
            chrome.runtime.sendMessage({'type': 'requestSucceeded'});
        }, function(response) {
            chrome.runtime.sendMessage({'type': 'requestFailed'});
            sendResponse('error');
            //clearBadgeStatus();
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
