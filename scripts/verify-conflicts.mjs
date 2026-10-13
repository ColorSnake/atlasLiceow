import assert from 'node:assert/strict';
const origin='http://127.0.0.1:8765';
async function post(path,data){const r=await fetch(origin+'/api/'+path,{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(data)});return {status:r.status,body:await r.json()}}
for(const source of ['oto','wasza']){const r=await post('import/preview',{source,year:2026});assert.equal(r.status,200,JSON.stringify(r.body));console.log(source,'2026 preview',r.body.total);}
const a=await post('import/preview',{source:'oto',year:2024}),b=await post('import/preview',{source:'oto',year:2024});assert.equal(a.status,200);assert.equal(b.status,200);
assert.equal((await post('import/commit',{id:a.body.id})).status,200);
assert.equal((await post('import/commit',{id:b.body.id})).status,409);
const invalid=await post('import/preview',{source:'oto',year:2027});assert.equal(invalid.status,400);console.log('Stale preview rejected; absent future edition rejected without save.');
