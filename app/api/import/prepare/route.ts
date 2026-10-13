import {getDraft,loadData,json,checkWrite,readBody} from '../../../../server/store';
import {mergeRanking} from '../../../../server/rankings.mjs';
export async function POST(request:Request){
 try{checkWrite(request);const {id,mappings}=await readBody(request),draft=await getDraft(id),state=await loadData();
 if((state.revisions[draft.parsed.year]||0)!==draft.revision)return json({error:'Rocznik zmienił się od pobrania podglądu. Pobierz go ponownie.'},409);
 return json({dataset:mergeRanking(draft.parsed,state.datasets,mappings||{})});
 }catch(error){return json({error:error instanceof Error?error.message:'Nie udało się przygotować JSON.'},400)}
}
