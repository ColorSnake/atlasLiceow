'use strict';
(() => {
  const downloadFile = (name, text, type) => {
    const url = URL.createObjectURL(new Blob([text], {type})), link = document.createElement('a');
    link.href = url; link.download = name; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  };
  function csvFor(data) {
    const columns = ['miasto','typ_szkoly','rok_rankingu','wydawca','zakres','id_szkoly','nazwa_szkoly','miejsce','punkty','rok_matury','zdawalnosc_proc','polski_proc','matematyka_proc','angielski_proc','adres','szerokosc','dlugosc','typ','dla_doroslych','rok_oferty','profile','zrodlo_rankingu'];
    const cell = value => '"' + String(value ?? '').replace(/^[\s]*[=+@-]/, match => "'" + match).replace(/"/g, '""') + '"';
    const rows = [columns];
    for (const school of data.schools) for (const [key, rank] of Object.entries(school.rankings)) {
      if (!rank) continue;
      rows.push([cityInfo.name,'liceum',data.rankingYear,data.sources[key].name,data.sources[key].scope,school.id,school.name,rank.rank,rank.score,school.examYear,rank.passRate,rank.polish,rank.math,rank.english,school.address,school.coords?.[0],school.coords?.[1],school.type,school.adult?'tak':'nie',school.profileYear,school.profiles.join(' | '),rank.sourceUrl||data.sources[key].url]);
    }
    return '\uFEFF' + rows.map(row => row.map(cell).join(';')).join('\r\n') + '\r\n';
  }

  const atlasMain = document.querySelector('main'), nav = document.createElement('nav');
  nav.className = 'data-tabs'; nav.setAttribute('aria-label', 'Widoki aplikacji');
  nav.innerHTML = '<button id="atlasTab" class="active" aria-pressed="true">Mapa i rankingi</button><button id="dataTab" aria-pressed="false">Dane · eksport</button>';
  atlasMain.before(nav);
  const dataPanel = document.createElement('section');
  dataPanel.id = 'dataPanel'; dataPanel.hidden = true; atlasMain.after(dataPanel);
  dataPanel.innerHTML = `<div class="data-heading"><p class="eyebrow">DANE RANKINGOWE</p><h2>Pobierz wybrany rocznik.</h2><p>Zachowaj dane do własnych porównań i analiz.</p></div>
<section class="data-card"><h3>Eksport rankingów</h3><p>Plik obejmuje wszystkie szkoły i rankingi wybranego roku, również licea dla dorosłych. Filtry mapy nie ograniczają eksportu.</p><label>Rocznik<select id="exportYear"></select></label><div class="data-actions"><button id="exportCSV" class="data-primary">Pobierz CSV</button><button id="exportJSON" class="small-button">Pobierz JSON</button></div><p class="note">CSV: jeden wiersz na szkołę i wydawcę, separator średnik, UTF-8 dla polskich znaków. JSON zachowuje pełną strukturę rocznika.</p></section>`;
  $('exportYear').innerHTML = Object.keys(datasets).sort((a, b) => b - a).map(value => `<option>${value}</option>`).join('');
  $('exportYear').value = year;
  const viewData = show => {
    atlasMain.hidden = show; dataPanel.hidden = !show;
    for (const [id, active] of [['atlasTab', !show], ['dataTab', show]]) {
      $(id).classList.toggle('active', active); $(id).setAttribute('aria-pressed', String(active));
    }
    if (show) {
      $('exportYear').innerHTML = Object.keys(datasets).sort((a,b)=>b-a).map(value=>`<option>${value}</option>`).join('');
      $('exportYear').value = year;
      dataPanel.querySelector('h2').textContent = `${cityInfo.name} · pobierz wybrany rocznik.`;
    }
    else if (map) requestAnimationFrame(() => map.invalidateSize());
  };
  $('atlasTab').onclick = () => viewData(false);
  $('dataTab').onclick = () => viewData(true);
  $('exportCSV').onclick = () => {
    const selectedYear = $('exportYear').value;
    downloadFile(`licea-${city}-${selectedYear}.csv`, csvFor(datasets[selectedYear]), 'text/csv;charset=utf-8');
  };
  $('exportJSON').onclick = () => {
    const selectedYear = $('exportYear').value;
    downloadFile(`rankings-${city}-${selectedYear}.json`, JSON.stringify(datasets[selectedYear], null, 2), 'application/json');
  };
  if (window.DATA_API_ERROR) {
    const warning = document.createElement('p');
    warning.className = 'data-error'; warning.textContent = window.DATA_API_ERROR; nav.before(warning);
  }
})();
