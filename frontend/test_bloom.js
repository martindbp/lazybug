var bloom = require('./bloom');
console.log(bloom);

let n = 134191;
let k = 23
const filter1 = new bloom.BloomFilter(n, k);
const filter2 = new bloom.BloomFilter(n, k);

for (let i = 0; i < 2000; i++) {
    filter1.add(i);
    //console.log(i+1, filter1.size());
}

for (let i = 1000; i < 3000; i++) {
    filter2.add(i);
    //console.log(i+1, filter2.size());
}

//console.log(filter1.intersectionCount(filter2));
//console.log(filter2.intersectionCount(filter1));

//console.log(filter1.union(filter2).size());
//console.log(filter1.buckets.length);
//console.log(filter1.buckets);

//const buf = new Uint8Array(filter1.buckets.buffer);
//console.log(buf);
//const hex = Buffer.from(buf).toString('hex');
//console.log(hex.length);
//var buf = Buffer.from(filter1.buckets);
//console.log(buf);

//const s = buf.toString('hex');
//console.log(s.length, s.length * 4)
//console.log(s.slice(0, 10))
//const asd = s.match(/../g);
//console.log(asd.length * 32)
//const arr = new Int32Array(asd.map(h=>parseInt(h, 32)));
//console.log(arr.length * 32)
////console.log(asd.slice(10));
//console.log(filter1.buckets.slice(10));
//console.log(arr.slice(10));
//console.log(filter1.intersection(filter2));

const uint8 = new Uint8Array(filter1.buckets.buffer);
const buf = Buffer.from(uint8);
const hex = buf.toString('hex');

const arr = new Uint8Array(hex.match(/../g).map(h=>parseInt(h, 16)));
const arr32 = new Int32Array(arr.buffer);
console.log(uint8.slice(0, 10))
console.log(arr.slice(0, 10))

console.log(filter1.buckets.slice(0, 10))
console.log(arr32.slice(0, 10))
