const fs = require('fs')
const bloom = require('./frontend/bloom');

const words = fs.readFileSync(process.argv[2], 'utf8').split('\n');
const outPath = process.argv[3];
const n = parseInt(process.argv[4]);
const k = parseInt(process.argv[5]);

const filter = new bloom.BloomFilter(n, k);
for (const word of words) {
    filter.add(word);
}

const uint8 = new Uint8Array(filter.buckets.buffer);
const buf = Buffer.from(uint8);
const hex = buf.toString('hex');

fs.writeFile(outPath, hex, function (err, data) {
    if (err) {
        return console.log(err);
    }
});
