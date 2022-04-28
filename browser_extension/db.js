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
        log: '[captionId+captionHash+sessionTime], sessionTime, hasStarEvents',
    });

    personalDb.version(2).stores({
        states: 'id',
        other: 'id',
        log: '[captionId+captionHash+sessionTime], sessionTime, captionHash, *eventIds',
    })
    .upgrade(tx => {
        return tx.table("log").toCollection().modify(item => {
            item.eventIds = [];
            item.eventData = [];
            for (const event of item.events) {
                item.eventIds.push(event[0]);
                item.eventData.push(event.slice(1));
            }

            delete item.events;
            delete item.hasStarEvents;
    });
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
