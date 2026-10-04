'use strict';
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const normalize=value=>String(value).toLocaleLowerCase('pl').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ł/g,'l');
const schools=window.SCHOOL_DATA.schools;
const sources={
 wasza:{name:'WaszaEdukacja',scope:'w Krakowie',url:'https://waszaedukacja.pl/ranking/krakow/licea',description:'Ranking łączy wyniki egzaminów, osiągnięcia olimpijskie i edukacyjną wartość dodaną (EWD). Prezentujemy opublikowane miejsca i punkty, bez własnego przeliczania.',digits:3},
 pers:{name:'Perspektywy',scope:'w Polsce',url:'https://licea.perspektywy.pl/rankingi/ranking-glowny-liceow/',description:'Olimpiady: 25%, matura obowiązkowa: 30%, matura dodatkowa: 45%. Edycja 2026 opiera się na osiągnięciach 2024/2025. Nie obejmuje wyników matury IB. Miejsca ex aequo zachowujemy zgodnie z tabelą wydawcy.',digits:2},
 oto:{name:'otouczelnie',scope:'w Krakowie',url:'https://www.otouczelnie.pl/ranking/208/Ranking-liceow-w-Krakowie-2026',description:'Domyślny ranking 2026 na podstawie matury 2025: połowa procentowej zdawalności + średnie wyniki z polskiego, matematyki i angielskiego na poziomie podstawowym. Prezentujemy oryginalne miejsca wydawcy, także remisy.',digits:2}
};
let source='wasza',selected=null,visible=[],map=null,markers=new Map(),layer=null;
const fmt=(n,d=2)=>Number(n).toLocaleString('pl-PL',{maximumFractionDigits:d,minimumFractionDigits:d});
const safeURL=url=>{try{const u=new URL(url);return ['https:','http:'].includes(u.protocol)?esc(u.href):'#'}catch{return '#'}};
const external=(url,text,cls='')=>`<a href="${safeURL(url)}" target="_blank" rel="noopener noreferrer" class="${cls}">${esc(text)}</a>`;
for(const tag of [...new Set(schools.flatMap(s=>s.tags))].sort((a,b)=>a.localeCompare(b,'pl'))){const option=document.createElement('option');option.value=tag;option.textContent=tag;$('profile').append(option)}
if(window.L){
 map=L.map('map',{zoomControl:false}).setView([50.066,19.965],12);
 L.control.zoom({position:'bottomright'}).addTo(map);
 const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
 let failures=0;tiles.on('tileerror',()=>{if(++failures>=3){$('mapError').hidden=false;$('mapError').textContent='Nie udało się pobrać części podkładu mapy. Sprawdź połączenie z internetem. Lista szkół i dane działają niezależnie.'}});
 tiles.on('tileload',()=>{failures=0;$('mapError').hidden=true});
 layer=L.markerClusterGroup({maxClusterRadius:38,showCoverageOnHover:false,spiderfyDistanceMultiplier:1.8,animate:false,iconCreateFunction:cluster=>L.divIcon({className:'school-cluster',html:`<b>${cluster.getChildCount()}</b><small>szkoły</small>`,iconSize:[46,46]})}).addTo(map);
}else{$('mapError').hidden=false;$('mapError').textContent='Biblioteka mapy nie została wczytana. Nadal możesz korzystać z listy szkół.'}
function filtered(){const query=normalize($('search').value.trim());return schools.filter(s=>s.rankings[source]&&($('adults').checked||!s.adult)&&(!$('type').value||s.type===$('type').value)&&(!$('profile').value||s.tags.includes($('profile').value))&&(!query||normalize(s.name+' '+s.address).includes(query))).sort((a,b)=>parseInt(a.rankings[source].rank)-parseInt(b.rankings[source].rank)||b.rankings[source].score-a.rankings[source].score)}
function icon(s){return L.divIcon({className:'number-marker'+(s.id===selected?' is-selected':''),html:`<div><span>${esc(s.rankings[source].rank)}</span></div>`,iconSize:[34,40],iconAnchor:[17,39]})}
function render(){
 visible=filtered();if(selected&&!visible.some(s=>s.id===selected))closeDetail();
 const info=sources[source];$('numberExplanation').textContent=`Numery = miejsca ${info.scope}${source==='pers'?' · „=” oznacza ex aequo':''}`;
 $('count').textContent=`${visible.length} ${visible.length===1?'szkoła':'szkół'}`;
 const mapped=visible.filter(s=>s.coords);$('mapCount').textContent=`${mapped.length} NA MAPIE`;
 $('coverage').textContent=`${visible.length-mapped.length} bez lokalizacji w tym widoku`;
 $('list').innerHTML=visible.length?visible.map(s=>{const r=s.rankings[source];return `<button class="school-row${s.id===selected?' active':''}" data-id="${esc(s.id)}" aria-pressed="${s.id===selected}"><span class="rank-badge">${esc(r.rank)}</span><span><span class="row-name">${esc(s.name)}</span><span class="row-address">${esc(s.address||'Brak potwierdzonego adresu')}${!s.coords?' · brak na mapie':''}</span><span class="row-points">${fmt(r.score,info.digits)} pkt · ${esc(info.name)}</span></span></button>`}).join(''):'<div class="empty-results">Brak szkół pasujących do filtrów.<br>Zmień kryteria lub wyczyść filtry.</div>';
 if(map){layer.clearLayers();markers.clear();for(const s of mapped){
 const marker=L.marker(s.coords,{icon:icon(s),title:`${s.rankings[source].rank}. ${s.name}`,alt:`${s.name}, miejsce ${s.rankings[source].rank} ${info.scope}`,keyboard:true,riseOnHover:true,zIndexOffset:s.id===selected?1000:0}).addTo(layer);
 marker.bindTooltip(esc(s.name),{direction:'top',offset:[0,-36]});marker.on('click',()=>selectSchool(s.id));markers.set(s.id,marker);
 }}
 if(selected)renderDetail(schools.find(s=>s.id===selected));
}
function fit(){if(map&&visible.some(s=>s.coords)){map.fitBounds(L.latLngBounds(visible.filter(s=>s.coords).map(s=>s.coords)),{padding:[50,70],maxZoom:14})}}
function selectSchool(id){const s=visible.find(x=>x.id===id);if(!s)return;selected=id;render();$('detail').classList.add('open');if(map&&s.coords){map.setView(s.coords,Math.max(map.getZoom(),14),{animate:false});layer.zoomToShowLayer(markers.get(id),()=>markers.get(id)?.openTooltip())}const row=[...$('list').querySelectorAll('[data-id]')].find(el=>el.dataset.id===id);if(row){const list=$('list');list.scrollTop=Math.max(0,row.offsetTop-list.offsetTop-10)}$('detail').scrollTop=0}
const emptyDetail=$('detail').innerHTML;
function closeDetail(){selected=null;$('detail').classList.remove('open');$('detail').innerHTML=emptyDetail}
function renderDetail(s){
 const r=s.rankings.oto;const p=s.rankings.pers;
 $('detail').innerHTML=`<div class="detail-top"><div class="detail-meta"><span class="type-badge">${esc(s.type)}${s.adult?' · dla dorosłych':''}</span><button class="icon-button" id="closeDetail" aria-label="Zamknij szczegóły szkoły">×</button></div><h2>${esc(s.name)}</h2><div class="address">${esc(s.address||'Brak potwierdzonego adresu')}${!s.coords?'<br>Brak potwierdzonej lokalizacji na mapie.':''}</div><div class="detail-links">${s.website?external(s.website,'Strona szkoły ↗'):''}${s.coords?external(`https://www.google.com/maps/dir/?api=1&destination=${s.coords.join(',')}`,'Sprawdź dojazd ↗','secondary'):''}</div></div>
 <div class="detail-section"><h3 class="section-title">Miejsca w rankingach 2026</h3><div class="rank-comparison">${Object.entries(sources).map(([k,src])=>`<div class="rank-cell${k===source?' current':''}"><small>${esc(src.name)}</small><strong>${esc(s.rankings[k]?.rank??'—')}</strong><em>${src.scope}</em></div>`).join('')}</div><p class="note">Perspektywy: miejsce ogólnopolskie. Pozostałe: Kraków. „—” oznacza brak danych.</p></div>
 <div class="detail-section"><h3 class="section-title">Matura 2025 · poziom podstawowy</h3>${r?[['Język polski',r.polish],['Matematyka',r.math],['Język angielski',r.english]].map(([label,value])=>`<div class="score-line"><span>${label}</span><b>${fmt(value)}%</b></div><div class="bar"><i style="width:${value}%"></i></div>`).join('')+`<div class="score-line" style="margin-top:16px"><span>Zdawalność matury</span><b>${fmt(r.passRate)}%</b></div>${external(r.url,'Wyniki w otouczelnie ↗','source-link')}`:'<p class="note">Brak danych w tym źródle.</p>'}</div>
 <div class="detail-section"><h3 class="section-title">Profile i rozszerzenia</h3><div class="tags">${s.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>${s.specialization?`<p class="note">${esc(s.specialization)}</p>${external(s.specializationSource,'Informacje o specjalizacji ↗','source-link')}`:''}<p class="note" style="margin-bottom:10px">Oferta: ${esc(s.profileYear)} · ${s.profileSource.includes('waszaedukacja')?'WaszaEdukacja':'otouczelnie'}</p>${s.profiles.length?`<ul class="profile-list">${s.profiles.map(c=>`<li>${esc(c)}</li>`).join('')}</ul>`:'<p class="note">Brak opublikowanych profili w pobranych danych. Sprawdź ofertę na stronie szkoły.</p>'}${external(s.profileSource,'Źródło oferty klas ↗','source-link')}<p class="note">Kategorie opisują zakres oferty, nie jakość nauczania. Potwierdź dostępność oddziałów u szkoły.</p></div>
 ${p?`<div class="detail-section"><h3 class="section-title">Perspektywy · historia w Polsce</h3><div class="history">${Object.entries(p.history).map(([year,rank])=>`<div><span>${year}</span><strong>${esc(rank)}</strong></div>`).join('')}</div><p class="note">Zmiany miejsc między latami nie są bezpośrednią miarą postępu uczniów.</p></div>`:''}
 <div class="detail-source">Zapis danych: 04.10.2026.<br>${s.coordSource?external(s.coordSource,'Źródło współrzędnych ↗'):''}${s.addressSource?' · '+external(s.addressSource,'Potwierdzenie adresu ↗'):''}<br>${Object.entries(sources).filter(([k])=>s.rankings[k]).map(([k,v])=>external(v.url,v.name+' ↗')).join(' · ')}</div>`;
 $('closeDetail').onclick=()=>{closeDetail();render()};
}
$('list').addEventListener('click',e=>{const row=e.target.closest('[data-id]');if(row)selectSchool(row.dataset.id)});
$('ranking').addEventListener('change',()=>{source=$('ranking').value;render();fit()});
for(const id of ['profile','type','adults'])$(id).addEventListener('change',()=>{render();fit()});
$('search').addEventListener('input',()=>render());
$('reset').onclick=()=>{$('search').value='';$('type').value='';$('profile').value='';$('adults').checked=false;render();fit()};$('fit').onclick=fit;
$('sourcesBtn').onclick=()=>$('sources').showModal();$('closeSources').onclick=()=>$('sources').close();$('sources').addEventListener('click',e=>{if(e.target===$('sources')){const r=$('sources').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('sources').close()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('sources').open){closeDetail();render()}});
$('sourceContent').innerHTML=Object.entries(sources).map(([k,s])=>`<div class="source-card"><h3>${external(s.url,s.name+' ↗')}</h3><p>${s.description}</p><p class="note">W bazie: ${schools.filter(s=>s.rankings[k]).length} szkół z tego rankingu.</p></div>`).join('');
$('dataCompleteness').textContent=`Baza: ${schools.length} szkół; ${schools.filter(s=>s.coords).length} lokalizacji; ${schools.filter(s=>s.profiles.length).length} kart z profilami. Szkoły bez współrzędnych pozostają na liście. To nie jest pełny rejestr wszystkich działających liceów.`;
render();fit();
// Optional page-scoped agent navigation; uses the exact same action as the list.
if(document.modelContext?.registerTool){try{Promise.resolve(document.modelContext.registerTool({name:'show_school',description:'Otwórz szczegóły szkoły widocznej w aktualnie wybranym rankingu i filtrach.',inputSchema:{type:'object',properties:{schoolId:{type:'string'}},required:['schoolId'],additionalProperties:false},annotations:{readOnlyHint:false},execute(input){if(!input||typeof input.schoolId!=='string'||!visible.some(s=>s.id===input.schoolId))throw new Error('Szkoła nie jest widoczna w obecnym widoku.');selectSchool(input.schoolId);return {schoolId:selected,ranking:source}}})).catch(()=>{})}catch{}}
