'use strict';
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const normalize=value=>String(value).toLocaleLowerCase('pl').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ł/g,'l');
const datasets=window.SCHOOL_DATASETS;
let year=String(Math.max(...Object.keys(datasets).map(Number)));
let dataset=datasets[year],schools=dataset.schools,sources=dataset.sources;
const dateLabel=date=>date.split('-').reverse().join('.');
const percentage=value=>value==null?'—':fmt(value)+'%';
let source='wasza',selected=null,visible=[],map=null,markers=new Map(),layer=null;
const fmt=(n,d=2)=>Number(n).toLocaleString('pl-PL',{maximumFractionDigits:d,minimumFractionDigits:d});
const safeURL=url=>{try{const u=new URL(url);return ['https:','http:'].includes(u.protocol)?esc(u.href):'#'}catch{return '#'}};
const external=(url,text,cls='')=>`<a href="${safeURL(url)}" target="_blank" rel="noopener noreferrer" class="${cls}">${esc(text)}</a>`;
function refreshMetadata(){
 $('year').innerHTML=Object.keys(datasets).sort((a,b)=>b-a).map(y=>`<option value="${y}">${y}</option>`).join('');$('year').value=year;
 $('yearNote').textContent=dataset.historical?'Archiwalne wyniki. Lokalizacje z bazy 2026; brak historycznych profili klas.':`Dostępne roczniki: ${Object.keys(datasets).sort().join(', ')}.`;
 $('editionLabel').textContent=`EDYCJA RANKINGÓW ${year}`;
 $('ranking').innerHTML=Object.entries(sources).map(([k,v])=>`<option value="${esc(k)}">${esc(v.name)} · ${year}</option>`).join('');
 if(!sources[source])source=Object.keys(sources)[0];$('ranking').value=source;
 const oldProfile=$('profile').value;
 $('profile').innerHTML='<option value="">Wszystkie profile</option>';
 for(const tag of [...new Set(schools.flatMap(s=>s.tags))].sort((a,b)=>a.localeCompare(b,'pl'))){const option=document.createElement('option');option.value=tag;option.textContent=tag;$('profile').append(option)}
 if([...$('profile').options].some(o=>o.value===oldProfile))$('profile').value=oldProfile;
 $('snapshotDate').textContent=`Dane zapisane ${dateLabel(dataset.updated)}`;
 $('snapshotInfo').textContent=`Edycja ${year}. Zapis danych: ${dateLabel(dataset.updated)}. Rok matury: ${dataset.examYear??'podany przy szkole / niepotwierdzony'}. Rok oferty klas podajemy osobno w każdej karcie. Zestaw nie aktualizuje się automatycznie.`;
 $('sourceContent').innerHTML=Object.entries(sources).map(([k,s])=>`<div class="source-card"><h3>${external(s.url,s.name+' ↗')}</h3><p>${esc(s.description)}</p><p class="note">W bazie edycji ${year}: ${schools.filter(s=>s.rankings[k]).length} szkół z tego rankingu.</p></div>`).join('');
 $('dataCompleteness').textContent=`Baza edycji ${year}: ${schools.length} szkół; ${schools.filter(s=>s.coords).length} lokalizacji; ${schools.filter(s=>s.profiles.length).length} kart z profilami. Szkoły bez współrzędnych pozostają na liście. To nie jest pełny rejestr wszystkich działających liceów.`;
}
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
function selectSchool(id){const s=visible.find(x=>x.id===id);if(!s)return;selected=id;render();$('detail').classList.add('open');if(map&&s.coords){map.setView(s.coords,Math.max(map.getZoom(),16),{animate:false});const marker=markers.get(id);if(marker&&map.hasLayer(marker))marker.openTooltip()}const row=[...$('list').querySelectorAll('[data-id]')].find(el=>el.dataset.id===id);if(row){const list=$('list');list.scrollTop=Math.max(0,row.offsetTop-list.offsetTop-10)}$('detail').scrollTop=0}
const emptyDetail=$('detail').innerHTML;
function closeDetail(){selected=null;$('detail').classList.remove('open');$('detail').innerHTML=emptyDetail}
function historyHTML(id,key){
 const years=Object.keys(datasets).map(Number).sort((a,b)=>a-b);
 const points=years.map(y=>{const d=datasets[y],s=d.schools.find(s=>s.id===id),r=s?.rankings[key];return {year:y,rank:r?.rank??null,url:d.sources[key]?.url}});
 if(key==='pers')for(const d of Object.values(datasets)){const s=d.schools.find(s=>s.id===id);for(const [y,rank] of Object.entries(s?.rankings.pers?.history??{})){const point=points.find(p=>p.year===Number(y));if(point&&point.rank===null&&rank!=='-'){point.rank=rank;point.url=d.sources.pers?.url;point.indirect=true}}}
 const present=points.filter(p=>p.rank!==null),max=Math.max(2,...present.map(p=>parseInt(p.rank))),x=i=>34+i*272/(years.length-1||1),y=r=>28+(parseInt(r)-1)*130/(max-1);
 let svg=`<svg class="rank-chart" viewBox="0 0 330 195" role="img" aria-label="Historia miejsc. Miejsce pierwsze u góry. Dokładne wartości w tabeli poniżej.">`;
 for(const rank of [...new Set([1,Math.round(max/2)||1,max])])svg+=`<path d="M34 ${y(rank)}H306" stroke="#e1e5e1"/><text x="27" y="${y(rank)+4}" text-anchor="end">${rank}</text>`;
 for(let i=0;i<points.length;i++){const p=points[i];svg+=`<text x="${x(i)}" y="181" text-anchor="middle">${String(p.year).slice(2)}</text>`;if(p.rank===null)continue;if(i&&points[i-1].rank!==null)svg+=`<path d="M${x(i-1)} ${y(points[i-1].rank)}L${x(i)} ${y(p.rank)}" stroke="#237762" stroke-width="2.5"/>`;svg+=`<circle cx="${x(i)}" cy="${y(p.rank)}" r="4" fill="#237762"><title>${p.year}: miejsce ${esc(p.rank)}</title></circle>`}
 svg+='</svg>';
 return `<p class="note">${key==='pers'?'Miejsca w Polsce':'Miejsca w Krakowie'} · 1. miejsce u góry</p>${present.length?svg:'<p class="note">Brak historii w tym źródle.</p>'}<details class="history-values"><summary>Dokładne miejsca i źródła</summary><table><thead><tr><th>Rok</th><th>Miejsce</th><th>Źródło</th></tr></thead><tbody>${points.map(p=>`<tr><td>${p.year}</td><td>${esc(p.rank??'—')}</td><td>${p.rank!==null&&p.url?external(p.url,p.indirect?'Tabela historii 2026 ↗':'Ranking ↗'):'Brak danych'}</td></tr>`).join('')}</tbody></table></details><p class="note">Przerwa oznacza brak danych. Zakres szkół i metodologia zmieniają się między latami; zmiana miejsca nie jest bezpośrednią miarą postępu uczniów.</p>`;
}
function renderDetail(s){
 const r=s.rankings.oto;const p=s.rankings.pers;
 $('detail').innerHTML=`<div class="detail-top"><div class="detail-meta"><span class="type-badge">${esc(s.type)}${s.adult?' · dla dorosłych':''}</span><button class="icon-button" id="closeDetail" aria-label="Zamknij szczegóły szkoły">×</button></div><h2>${esc(s.name)}</h2><div class="address">${esc(s.address||'Brak potwierdzonego adresu')}${!s.coords?'<br>Brak potwierdzonej lokalizacji na mapie.':''}</div><div class="detail-links">${s.website?external(s.website,'Strona szkoły ↗'):''}${s.coords?external(`https://www.google.com/maps/dir/?api=1&destination=${s.coords.join(',')}`,'Sprawdź dojazd ↗','secondary'):''}</div></div>
 <div class="detail-section"><h3 class="section-title">Miejsca w rankingach ${year}</h3><div class="rank-comparison">${Object.entries(sources).map(([k,src])=>`<div class="rank-cell${k===source?' current':''}"><small>${esc(src.name)}</small><strong>${esc(s.rankings[k]?.rank??'—')}</strong><em>${esc(src.scope)}</em></div>`).join('')}</div><p class="note">Perspektywy: miejsce ogólnopolskie. Pozostałe: Kraków. „—” oznacza brak danych.</p></div>
 <div class="detail-section"><h3 class="section-title">Matura ${esc(s.examYear??'— rok niepotwierdzony')} · poziom podstawowy</h3>${r?[['Język polski',r.polish],['Matematyka',r.math],['Język angielski',r.english]].map(([label,value])=>`<div class="score-line"><span>${label}</span><b>${percentage(value)}</b></div><div class="bar"><i style="width:${value??0}%"></i></div>`).join('')+`<div class="score-line" style="margin-top:16px"><span>Zdawalność matury</span><b>${percentage(r.passRate)}</b></div>${external(r.sourceUrl||r.url,'Wyniki w otouczelnie ↗','source-link')}`:'<p class="note">Brak danych w tym źródle.</p>'}</div>
 <div class="detail-section"><h3 class="section-title">Profile i rozszerzenia</h3><div class="tags">${s.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>${s.specialization?`<p class="note">${esc(s.specialization)}</p>${external(s.specializationSource,'Informacje o specjalizacji ↗','source-link')}`:''}<p class="note" style="margin-bottom:10px">Oferta: ${esc(s.profileYear)} · ${s.profileSource.includes('waszaedukacja')?'WaszaEdukacja':'otouczelnie'}</p>${s.profiles.length?`<ul class="profile-list">${s.profiles.map(c=>`<li>${esc(c)}</li>`).join('')}</ul>`:'<p class="note">Brak opublikowanych profili w pobranych danych. Sprawdź ofertę na stronie szkoły.</p>'}${external(s.profileSource,'Źródło oferty klas ↗','source-link')}<p class="note">Kategorie opisują zakres oferty, nie jakość nauczania. Potwierdź dostępność oddziałów u szkoły.</p></div>
 ${p?`<div class="detail-section"><h3 class="section-title">Perspektywy · historia w Polsce</h3><div class="history">${Object.entries(p.history??{}).map(([year,rank])=>`<div><span>${year}</span><strong>${esc(rank)}</strong></div>`).join('')}</div><p class="note">Zmiany miejsc między latami nie są bezpośrednią miarą postępu uczniów.</p></div>`:''}
 <div class="detail-source">Zapis danych: ${dateLabel(dataset.updated)}.<br>${s.coordSource?external(s.coordSource,'Źródło współrzędnych ↗'):''}${s.addressSource?' · '+external(s.addressSource,'Potwierdzenie adresu ↗'):''}<br>${Object.entries(sources).filter(([k])=>s.rankings[k]).map(([k,v])=>external(v.url,v.name+' ↗')).join(' · ')}</div>`;
 const chart=document.createElement('div');chart.className='detail-section';
 chart.innerHTML=`<h3 class="section-title">Historia miejsc · ${Math.min(...Object.keys(datasets))}–${Math.max(...Object.keys(datasets))}</h3><label for="historySource">Ranking na wykresie</label><select id="historySource"><option value="wasza">WaszaEdukacja · Kraków</option><option value="oto">otouczelnie · Kraków</option><option value="pers">Perspektywy · Polska</option></select><div id="historyChart"></div>`;
 $('detail').children[1].after(chart);$('historySource').value=source;
 const updateHistory=()=>{$('historyChart').innerHTML=historyHTML(s.id,$('historySource').value)};
 $('historySource').onchange=updateHistory;updateHistory();
 if(dataset.historical){
 const note=document.createElement('p');note.className='note';note.textContent=s.metadataAsOf?`Adres i mapa: stan z ${dateLabel(s.metadataAsOf)}, lokalizacja historyczna niepotwierdzona.`:'Brak potwierdzonych historycznych danych adresowych.';$('detail').firstElementChild.append(note);
 const profiles=[...$('detail').querySelectorAll('.detail-section')].find(e=>e.textContent.includes('Profile i rozszerzenia'));
 profiles.innerHTML='<h3 class="section-title">Profile i rozszerzenia</h3><p class="note">Nie pobrano historycznej oferty klas. Aktualnie zebrane profile można sprawdzić w edycji 2026.</p>';
 }
 $('closeDetail').onclick=()=>{closeDetail();render()};
}
$('year').addEventListener('change',()=>{
 year=$('year').value;dataset=datasets[year];schools=dataset.schools;sources=dataset.sources;
 closeDetail();refreshMetadata();render();fit();
});
$('list').addEventListener('click',e=>{const row=e.target.closest('[data-id]');if(row)selectSchool(row.dataset.id)});
$('ranking').addEventListener('change',()=>{source=$('ranking').value;render();fit()});
for(const id of ['profile','type','adults'])$(id).addEventListener('change',()=>{render();fit()});
$('search').addEventListener('input',()=>render());
$('reset').onclick=()=>{$('search').value='';$('type').value='';$('profile').value='';$('adults').checked=false;render();fit()};$('fit').onclick=fit;
$('sourcesBtn').onclick=()=>$('sources').showModal();$('closeSources').onclick=()=>$('sources').close();$('sources').addEventListener('click',e=>{if(e.target===$('sources')){const r=$('sources').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('sources').close()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('sources').open){closeDetail();render()}});
refreshMetadata();render();fit();
// Optional page-scoped agent navigation; uses the exact same action as the list.
if(document.modelContext?.registerTool){try{Promise.resolve(document.modelContext.registerTool({name:'show_school',description:'Otwórz szczegóły szkoły widocznej w aktualnie wybranym rankingu i filtrach.',inputSchema:{type:'object',properties:{schoolId:{type:'string'}},required:['schoolId'],additionalProperties:false},annotations:{readOnlyHint:false},execute(input){if(!input||typeof input.schoolId!=='string'||!visible.some(s=>s.id===input.schoolId))throw new Error('Szkoła nie jest widoczna w obecnym widoku.');selectSchool(input.schoolId);return {schoolId:selected,ranking:source,year:Number(year)}}})).catch(()=>{})}catch{}}
