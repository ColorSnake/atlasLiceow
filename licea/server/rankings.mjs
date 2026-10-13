export const normalize=value=>String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ł/gi,'l').toLowerCase().replace(/[^a-z0-9]/g,'');
const entities={amp:'&',quot:'"',apos:"'",lt:'<',gt:'>',nbsp:' ',oacute:'ó',Oacute:'Ó',aogon:'ą',eogon:'ę',lstrok:'ł',sacute:'ś',cacute:'ć',nacute:'ń',zacute:'ź',zdot:'ż'};
export const clean=html=>html.replace(/<[^>]*>/g,' ').replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi,(all,k)=>k[0]==='#'?String.fromCodePoint(parseInt(k.slice(k[1]?.toLowerCase()==='x'?2:1),k[1]?.toLowerCase()==='x'?16:10)):entities[k]??all).replace(/\s+/g,' ').trim();
const number=s=>{const n=Number(s.replace(/pkt|%/g,'').replace(',','.').trim());if(!Number.isFinite(n)||n<0)throw Error('Nieprawidłowa wartość w tabeli.');return n};
export function sourceURL(source,year){
 if(!['oto','wasza'].includes(source)||!Number.isInteger(year)||year<2017||year>new Date().getUTCFullYear()+1)throw Error('Wybierz wydawcę i rok od 2017 do przyszłego roku.');
 return source==='oto'?`https://www.otouczelnie.pl/ranking/208/Ranking-liceow-w-Krakowie-${year}`:`https://waszaedukacja.pl/ranking/krakow/licea/${year}`;
}
export function parseRanking(raw,source,year){
 const url=sourceURL(source,year),title=clean(raw.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]??'');
 const heading=clean(raw.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1]??'');
 if(![title,heading].some(label=>new RegExp(`\\b${year}\\b`).test(label)&&normalize(label).includes('krak')))throw Error('Strona nie potwierdza wybranego roku i Krakowa.');
 let table=raw;
 if(source==='wasza'){table=raw.match(/<table[^>]*id=["']tabela_rankingu["'][^>]*>([\s\S]*?)<\/table>/i)?.[1];if(!table)throw Error('Nie znaleziono tabeli rankingu. Wydawca mógł zmienić stronę.');}
 const rows=[];
 for(const match of table.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)){
  const cells=[...match[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)].map(x=>x[1]),v=cells.map(clean);
  if(source==='oto'?(cells.length!==7||!cells[1].includes('table-href')):(![3,4].includes(cells.length)||!/^\d+$/.test(v[0])||!v.at(-1).includes('pkt')))continue;
  const nameCell=source==='oto'?1:cells.length-2,href=cells[nameCell].match(/href=["']([^"']+)/i)?.[1];
  const row={rank:Number(v[0]),name:v[nameCell],url:href?new URL(clean(href),url).href:null,sourceUrl:url,score:number(v.at(-1))};
  if(!Number.isInteger(row.rank)||row.rank<1||!row.name)throw Error('Nieprawidłowa pozycja rankingu.');
  if(source==='oto'){
   ['passRate','polish','math','english'].forEach((k,i)=>{row[k]=number(v[i+2]);if(row[k]>100)throw Error('Wynik procentowy poza zakresem.');});
   if(Math.abs(row.score-(row.passRate/2+row.polish+row.math+row.english))>.02)throw Error('Zmieniła się metoda obliczania punktów. Import wymaga sprawdzenia.');
  }else row.national=cells.length===4?number(v[1]):null;
  rows.push(row);
 }
 const text=clean(raw);let examYear=null;
 if(source==='oto'){
  const expected=Number(text.match(/Liczba szkół spełniających kryteria:\s*(\d+)/)?.[1]);
  examYear=Number(text.match(/Wybrane kryteria rankingu\s*-\s*wyniki matury (\d{4})/)?.[1]);
  if(rows.length!==expected||!examYear||examYear>=year)throw Error('Niepełna tabela lub niepotwierdzony rok matury.');
 }
 if(!rows.length||rows[0].rank!==1||rows.length>500)throw Error('Brak pełnej tabeli zaczynającej się od miejsca 1.');
 if(rows.some((r,i)=>i&&r.rank<rows[i-1].rank))throw Error('Nieprawidłowa kolejność miejsc.');
 const identifiers=rows.map(r=>r.url||normalize(r.name));if(new Set(identifiers).size!==rows.length)throw Error('Powtórzona szkoła w tabeli.');
 return {source,year,url,examYear,rows};
}
export function identifyRows(parsed,datasets){
 const names=new Map(),urls=new Map(),catalog=new Map();
 const add=(map,key,id)=>{if(!key)return;const ids=map.get(key)||new Set();ids.add(id);map.set(key,ids)};
 for(const d of Object.values(datasets).sort((a,b)=>a.rankingYear-b.rankingYear))for(const s of d.schools){
  catalog.set(s.id,s);add(names,normalize(s.name),s.id);
  for(const r of Object.values(s.rankings)){if(r){add(urls,r.url,s.id);add(names,normalize(r.name||s.name),s.id);}}
 }
 return {rows:parsed.rows.map((r,index)=>{const ids=urls.get(r.url)||names.get(normalize(r.name));return {...r,index,schoolId:ids?.size===1?[...ids][0]:null}}),choices:[...catalog.values()].map(s=>({id:s.id,name:s.name}))};
}
export function mergeRanking(parsed,datasets,mappings={}){
 const existing=datasets[parsed.year],data=existing?structuredClone(existing):{schemaVersion:1,rankingYear:parsed.year,examYear:null,updated:'',historical:true,sources:{},schools:[]};
 const known=new Map();for(const d of Object.values(datasets).sort((a,b)=>a.rankingYear-b.rankingYear))for(const s of d.schools)known.set(s.id,{...s,metadataAsOf:s.metadataAsOf||d.updated});
 const rows=identifyRows(parsed,datasets).rows,seen=new Set(),schools=new Map(data.schools.map(s=>[s.id,s]));
 for(const s of schools.values())delete s.rankings[parsed.source];
 for(const r of rows){
  let id=r.schoolId||mappings[r.index];
  if(!id)throw Error('Przypisz wszystkie nierozpoznane szkoły przed zapisem.');
  if(id==='__new__')id=`import-${parsed.source}-${normalize(r.url?.split('/').filter(Boolean).at(-1)||r.name)}`;
  else if(!known.has(id))throw Error('Nieprawidłowe przypisanie szkoły.');
  if(seen.has(id))throw Error('Dwie pozycje przypisano do tej samej szkoły.');seen.add(id);
  if(!schools.has(id)){
   const s=known.get(id);
   schools.set(id,{id,name:r.name,address:s?.address||'',coords:s?.coords||null,type:s?.type||'Brak danych',adult:s?.adult??/doros/i.test(r.name),examYear:data.examYear,profileYear:'Brak oferty dla tej edycji',profileSource:'',profiles:[],tags:[],rankings:{},metadataAsOf:s?.metadataAsOf||null});
  }
  const {index,schoolId,...rank}=r;schools.get(id).rankings[parsed.source]=rank;
 }
 if(parsed.source==='oto'){data.examYear=parsed.examYear;for(const s of schools.values())s.examYear=parsed.examYear;}
 data.schools=[...schools.values()].filter(s=>Object.values(s.rankings).some(Boolean));data.updated=new Date().toISOString().slice(0,10);
 data.sources[parsed.source]={name:parsed.source==='oto'?'otouczelnie':'WaszaEdukacja',scope:'w Krakowie',url:parsed.url,digits:parsed.source==='oto'?2:3,description:`Edycja ${parsed.year}. Import ${data.updated}: ${rows.length} pozycji. Zachowano miejsca i punkty wydawcy. Zakres szkół i metodologia mogą zmieniać się między latami.`+(parsed.examYear?` Wyniki matury ${parsed.examYear}.`:'')};
 return data;
}
export function summarize(parsed,datasets){
 const identified=identifyRows(parsed,datasets),old=datasets[parsed.year]?.schools||[],prior=new Map(old.filter(s=>s.rankings[parsed.source]).map(s=>[s.id,s.rankings[parsed.source]])),seen=new Set(identified.rows.map(r=>r.schoolId).filter(Boolean));
 return {...identified,total:parsed.rows.length,added:identified.rows.filter(r=>!r.schoolId||!prior.has(r.schoolId)).length,changed:identified.rows.filter(r=>{const p=prior.get(r.schoolId);return p&&(String(p.rank)!==String(r.rank)||p.score!==r.score)}).length,removed:[...prior.keys()].filter(id=>!seen.has(id)).length};
}
