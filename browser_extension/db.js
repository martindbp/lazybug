try {
    importScripts('dexie.min.js');
    importScripts('dexie-export-import.js');
} catch (e) {
    console.error(e);
}

const PERSONAL_DB_VERSIONS = {
    '1': function(personalDb) {
        personalDb.version(1).stores({
            states: 'id',
            other: 'id',
            log: '[captionId+captionHash+sessionTime], sessionTime, captionHash, *eventIds, synced',
        });
    },
    '2': function(personalDb) {
        personalDb.version(2).stores({
            other: 'id',
        }).upgrade (trans => {
            return trans.other.toCollection().modify(item => {
                if (item.id === 'options') {
                    item.value.autoPause = item.value.autoPause ? 'basic' : 'off';
                    item.value.WPSThreshold = 2.0;
                }
            });
        });
    }
};

function initPersonalDb(untilVersion = null) {
    const personalDb = new Dexie('zimuai-personal');
    applyDbVersions(personalDb, PERSONAL_DB_VERSIONS, null, untilVersion);
    return personalDb;
}

function applyDbVersions(db, dbVersions, fromVersion = null, untilVersion = null) {
    let versionNumbers = Object.keys(dbVersions).map((v) => parseInt(v));
    versionNumbers.sort(function(a, b) {
      return a - b;
    });

    for (const version of versionNumbers) {
        if (fromVersion !== null && version < fromVersion) continue;
        if (untilVersion !== null && version > untilVersion) continue;
        console.log('Applying database version', version, 'for db', db.name);
        dbVersions[version.toString()](db);
    }
}

function initCacheDb() {
    const cacheDb = new Dexie('zimuai-cache');
    cacheDb.version(1).stores({
        network: 'id',
    });

    return cacheDb;
}
