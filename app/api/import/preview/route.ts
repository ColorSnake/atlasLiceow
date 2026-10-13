import {env} from 'cloudflare:workers';
import {loadData,json,checkWrite,readBody} from '../../../../server/store';
import {sourceURL,parseRanking,summarize} from '../../../../server/rankings.mjs';
export async function POST(request:Request){
 try{
  checkWrite(request);const {source,year}=await readBody(request),url=sourceURL(source,year);
  let target=url,response:Response|undefined;
  const signal=AbortSignal.timeout(25000);
  for(let attempt=0;attempt<3;attempt++){
   response=await fetch(target,{redirect:'manual',headers:{'User-Agent':'Mozilla/5.0 (compatible; KrakowSchoolAtlas/1.0)'},signal});
   if(![301,302,307,308].includes(response.status))break;
   const location=response.headers.get('location');if(!location)break;
   const next=new URL(location,target),base=new URL(url);
   const allowedPaths=[base.pathname.replace(/\/$/,''),...(source==='wasza'?['/ranking/krakow/licea']:[])];
   if(next.origin!==base.origin||next.search||!allowedPaths.includes(next.pathname.replace(/\/$/,'')))throw Error('Wydawca przekierował na inną stronę. Nie zapisano danych.');
   await response.body?.cancel();target=next.href;
  }
  if(!response)throw Error('Nie udało się pobrać strony.');
  if(!response.ok)throw Error(`Wydawca nie udostępnił danych (HTTP ${response.status}). Nie zapisano zmian. Możesz spróbować później.`);
  if(Number(response.headers.get('content-length'))>5000000)throw Error('Strona przekracza limit importu.');
  const reader=response.body!.getReader();let size=0;const chunks:Uint8Array[]=[];
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>5000000){await reader.cancel();throw Error('Strona przekracza limit importu.')}chunks.push(value);}
  const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
  const parsed=parseRanking(new TextDecoder().decode(bytes),source,year),state=await loadData(),summary=summarize(parsed,state.datasets),id=crypto.randomUUID();
  const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
  await env.DB!.batch([
   env.DB!.prepare('DELETE FROM import_drafts WHERE created < ?').bind(Date.now()-3600000),
   env.DB!.prepare('INSERT INTO import_drafts(id,payload,created) VALUES(?,?,?)').bind(id,JSON.stringify({parsed,revision:state.revisions[year]||0,sha256}),Date.now())
  ]);
  return json({id,year,source,url,sha256,...summary});
 }catch(error){return json({error:error instanceof Error?error.message:'Import nie powiódł się.'},400)}
}
