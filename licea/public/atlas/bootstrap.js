(async()=>{
 window.DATA_API_READY=false;
 try{const r=await fetch('/api/datasets',{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();const state=await r.json();if(state.catalog?.datasetsByCity){window.SCHOOL_CATALOG=state.catalog;window.SCHOOL_DATASETS=state.catalog.datasetsByCity[state.catalog.defaultCity];}else if(state.datasets){window.SCHOOL_DATASETS=state.datasets;window.SCHOOL_CATALOG={...window.SCHOOL_CATALOG,datasetsByCity:{...window.SCHOOL_CATALOG.datasetsByCity,krakow:state.datasets}};}else throw Error();window.DATA_API_READY=true;}
 catch{window.DATA_API_ERROR='Nie można pobrać danych. Wyświetlam kopię dołączoną do aplikacji.';}
 const script=document.createElement('script');script.src='app.js';script.onload=()=>{const gui=document.createElement('script');gui.src='data-manager.js';document.body.append(gui)};document.body.append(script);
})();
