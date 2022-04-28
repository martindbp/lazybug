try {
    importScripts('dexie.min.js');
    importScripts('dexie-export-import.js');
} catch (e) {
    console.error(e);
}

function initPersonalDb() {
    const personalDb = new Dexie('zimuai-personal');
    personalDb.version(1).stores({
        states: 'id',
        other: 'id',
        log: '[captionId+captionHash+sessionTime], sessionTime, captionHash, *eventIds',
    });

    return personalDb;
}

function initCacheDb() {
    const cacheDb = new Dexie('zimuai-cache');
    cacheDb.version(1).stores({
        network: 'id',
    });

    return cacheDb;
}
