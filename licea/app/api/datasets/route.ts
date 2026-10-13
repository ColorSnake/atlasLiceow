import {loadData,json} from '../../../server/store';
export async function GET(){try{return json(await loadData())}catch{return json({error:'Nie udało się odczytać zapisanych aktualizacji. Spróbuj ponownie.'},503)}}
