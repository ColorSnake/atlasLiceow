(async()=>{
 window.DATA_API_READY=false;
 try{const r=await fetch('/api/datasets',{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();const state=await r.json();if(!state.datasets)throw Error();window.SCHOOL_DATASETS=state.datasets;window.DATA_API_READY=true;}
 catch{window.DATA_API_ERROR='Nie można odczytać bazy. Wyświetlam kopię dołączoną do aplikacji; może nie zawierać ostatnich importów.';}
 const script=document.createElement('script');script.src='app.js';script.onload=()=>{const gui=document.createElement('script');gui.src='data-manager.js';document.body.append(gui)};document.body.append(script);
})();
