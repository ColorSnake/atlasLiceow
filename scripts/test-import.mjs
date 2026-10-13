import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parseRanking,identifyRows,mergeRanking,sourceURL} from '../server/rankings.mjs';
const seed=JSON.parse(fs.readFileSync(new URL('../server/seed.json',import.meta.url)));
const fixtures=JSON.parse(fs.readFileSync(new URL('../research/history/parsed.json',import.meta.url)));
for(const fixture of fixtures){
 const raw=fs.readFileSync(new URL('../research/history/'+fixture.cache,import.meta.url),'utf8');
 const parsed=parseRanking(raw,fixture.source,fixture.year);
 assert.equal(parsed.rows.length,fixture.rows.length);
 for(let i=0;i<parsed.rows.length;i++)for(const key of Object.keys(fixture.rows[i]))assert.deepEqual(parsed.rows[i][key],fixture.rows[i][key]);
 assert(identifyRows(parsed,seed).rows.every(r=>r.schoolId),'All historic identities should resolve');
 const before=JSON.stringify(seed),merged=mergeRanking(parsed,seed);
 assert.equal(JSON.stringify(seed),before);
 const others=Object.keys(seed[fixture.year].sources).filter(k=>k!==fixture.source);
 for(const key of others)for(const school of seed[fixture.year].schools){if(school.rankings[key])assert.deepEqual(merged.schools.find(s=>s.id===school.id).rankings[key],school.rankings[key]);}
 assert.throws(()=>parseRanking(raw,fixture.source,fixture.year+1));
}
const p=parseRanking(fs.readFileSync(new URL('../research/history/oto-2025.html',import.meta.url),'utf8'),'oto',2025);
const current=fs.readFileSync(new URL('../research/wasza-current.html',import.meta.url),'utf8');
assert.equal(parseRanking(current,'wasza',2026).rows.length,70);assert.throws(()=>parseRanking(current,'wasza',2027));
p.rows[0].name='Nowa szkoła';p.rows[0].url='https://www.otouczelnie.pl/new-school';
assert.throws(()=>mergeRanking(p,seed));
const merged=mergeRanking(p,seed,{0:'__new__'});assert.equal(merged.schools.find(s=>s.name==='Nowa szkoła').coords,null);
assert.throws(()=>mergeRanking(p,seed,{0:identifyRows(p,seed).rows[1].schoolId}));
assert.throws(()=>sourceURL('http://localhost',2025));
assert.throws(()=>sourceURL('oto',2000));
assert.throws(()=>parseRanking('<title>Ranking Kraków 2025</title>','oto',2025));
console.log('13 archived tables / 667 rows verified, identities, merge isolation, missing mappings and invalid pages passed.');
