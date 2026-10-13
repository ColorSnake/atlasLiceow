import {env} from 'cloudflare:workers';
import {getDraft,loadData,json,checkWrite,readBody} from '../../../../server/store';
import {mergeRanking} from '../../../../server/rankings.mjs';
export async function POST(request:Request){
 try{
  checkWrite(request);const {id,mappings}=await readBody(request),draft=await getDraft(id),state=await loadData(),year=draft.parsed.year;
  if((state.revisions[year]||0)!==draft.revision)return json({error:'Rocznik zmienił się od pobrania podglądu. Pobierz go ponownie.'},409);
  const data=mergeRanking(draft.parsed,state.datasets,mappings||{});
  data.importAudit={source:draft.parsed.source,url:draft.parsed.url,sha256:draft.sha256,importedAt:new Date().toISOString()};
  const saved=await env.DB!.prepare('INSERT INTO annual_snapshots(year,payload,revision) VALUES(?,?,1) ON CONFLICT(year) DO UPDATE SET payload=excluded.payload,revision=annual_snapshots.revision+1 WHERE annual_snapshots.revision=?').bind(year,JSON.stringify(data),draft.revision).run();
  if(saved.meta.changes!==1)return json({error:'Inny import zapisał ten rocznik. Pobierz podgląd ponownie.'},409);
  await env.DB!.prepare('DELETE FROM import_drafts WHERE id=?').bind(id).run();
  return json({year,dataset:data,message:'Zapisano rocznik. Mapa i wykresy korzystają z nowych danych.'});
 }catch(error){return json({error:error instanceof Error?error.message:'Nie udało się zapisać danych.'},400)}
}
