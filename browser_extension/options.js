let options = {};

function saveOptions() {
    chrome.storage.sync.set({
        options: options
    }, function() {});
}

function restoreOptionsFromStorage() {
    chrome.storage.sync.get('options', function(result) {
        // Transfer stored options
        Object.assign(options, result.options);
    });

    chrome.storage.local.getBytesInUse(null, function(bytesInUse) {
        document.getElementById('curr_cache_size').innerText = (bytesInUse / 1e6).toFixed(1) + ' MB';
        if (bytesInUse === 0) {
            document.getElementById('clear_cache').style.display = 'none';
        }
    });
}

function clearChromeStorage() {
    chrome.storage.local.clear(function() {
        var error = chrome.runtime.lastError;
        if (error) {
            console.error(error);
        } else {
            document.getElementById('clear_cache').style.display = 'none';
            document.getElementById('curr_cache_size').innerText = 'empty';
        }
    });
}

document.getElementById('clear_cache').addEventListener('click', clearChromeStorage);
document.getElementById('save').addEventListener('click', saveOptions);
document.addEventListener('DOMContentLoaded', function() {
    restoreOptionsFromStorage();
});
