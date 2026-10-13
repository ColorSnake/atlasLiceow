import { env } from 'cloudflare:workers';
import seeds from './seed.json';
export async function loadData(){
 if(!env.DB)throw Error('Baza danych jest niedostępna.');
 const result=await env.DB.prepare('SELECT year,payload,revision FROM annual_snapshots').all<{year:number,payload:string,revision:number}>();
 const datasets:Record<string,any>=structuredClone(seeds),revisions:Record<string,number>={};
 for(const row of result.results){datasets[row.year]=JSON.parse(row.payload);revisions[row.year]=row.revision;}
 return {datasets,revisions};
}
export function json(value:unknown,status=200){return Response.json(value,{status,headers:{'Cache-Control':'no-store'}})}
export function checkWrite(request:Request){
 const origin=request.headers.get('origin');
 if(origin!==new URL(request.url).origin)throw Error('Zapis wymaga żądania z tej aplikacji.');
 if(!request.headers.get('content-type')?.startsWith('application/json'))throw Error('Wymagane dane JSON.');
}
export async function readBody(request:Request){
 const raw=await request.text();if(raw.length>100000)throw Error('Żądanie jest zbyt duże.');return JSON.parse(raw);
}
export async function getDraft(id:string){
 if(typeof id!=='string'||!/^[0-9a-f-]{36}$/.test(id))throw Error('Nieprawidłowy identyfikator podglądu.');
 const draft=await env.DB!.prepare('SELECT payload,created FROM import_drafts WHERE id=?').bind(id).first<{payload:string,created:number}>();
 if(!draft||Date.now()-draft.created>3600000)throw Error('Podgląd wygasł. Pobierz ranking ponownie.');
 return JSON.parse(draft.payload);
}
