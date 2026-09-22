const $ = id => document.getElementById(id);
let catalog, result = null, view = 'detection', uploadURL = null, busy = false;
let noticeTimer;
function notice(text, error = false) {
  clearTimeout(noticeTimer); $('message').textContent = text; $('message').className = error ? 'error' : ''; $('message').hidden = false;
  noticeTimer = setTimeout(() => $('message').hidden = true, error ? 12000 : 5000);
}
async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}
function resetResult() {
  result = null; $('results').hidden = true; $('download-image').hidden = true;
  $('found').textContent = '— / 15'; $('keypoint-count').textContent = '—'; $('elapsed').textContent = '—';
  $('viewer-status').textContent = 'READY TO ANALYZE'; $('image-caption').textContent = 'Select a scene, then run detection to reveal matches.';
  $('metrics').textContent = '';
  document.querySelectorAll('#truth-options input').forEach(input => input.checked = false);
  setView('detection');
}
function sourceChanged() {
  if (uploadURL) URL.revokeObjectURL(uploadURL);
  const file = $('upload').files[0];
  uploadURL = file ? URL.createObjectURL(file) : null;
  const url = uploadURL || `/api/image/scenes/${$('scene').value}`;
  $('scene-thumb').src = url; $('result-image').src = url;
  $('upload-name').textContent = file ? file.name : '';
  $('clear-upload').hidden = !file; $('scene').disabled = Boolean(file);
  resetResult();
}
function setView(next) {
  view = next;
  document.querySelectorAll('[data-view]').forEach(button => {
    button.classList.toggle('active', button.dataset.view === view);
    button.setAttribute('aria-pressed', button.dataset.view === view);
  });
  $('match-options').hidden = view !== 'matches' || !result;
  if (!result) return;
  const key = view === 'matches' ? $('match-object').value : view;
  const url = key === 'original' ? result.original : result.images[key];
  $('result-image').src = url;
  $('result-image').alt = `${view} view for ${result.scene}`;
  $('download-image').href = url;
  $('download-image').download = `object-lab-${result.scene}-${key}.jpg`;
  $('download-image').hidden = false;
  $('image-caption').textContent = view === 'matches' ? `${key} → ${result.scene} · RANSAC inliers (up to 60 shown)` : `${result.scene} · ${result.width} × ${result.height} · ${view} view`;
}
function setBusy(value) {
  busy = value;
  if (value) { clearTimeout(noticeTimer); $('message').hidden = true; }
  ['run', 'upload', 'clear-upload', 'ratio', 'min-inliers', 'stitch'].forEach(id => $(id).disabled = value);
  $('scene').disabled = value || Boolean($('upload').files[0]);
  document.querySelectorAll('#stitch-scenes input').forEach(input => input.disabled = value);
}
function renderResults() {
  const found = result.objects.filter(obj => obj.detected).length;
  $('found').textContent = `${found} / ${result.objects.length}`;
  $('keypoint-count').textContent = result.keypoints.toLocaleString();
  $('elapsed').textContent = `${result.seconds}s`;
  $('viewer-status').textContent = 'ANALYSIS COMPLETE';
  $('results').hidden = false; $('result-rows').replaceChildren(); $('metrics').textContent = '';
  document.querySelectorAll('#truth-options input').forEach(input => input.checked = false);
  result.objects.forEach(obj => {
    const row = document.createElement('tr');
    [obj.name, obj.detected ? 'Detected' : 'Not confirmed', obj.matches, obj.inliers, `${Math.round(obj.inlier_ratio * 100)}%`].forEach((value, index) => {
      const td = document.createElement('td');
      if (index === 1) { const badge = document.createElement('span'); badge.className = `badge ${obj.detected ? 'yes' : ''}`; badge.textContent = value; td.append(badge); }
      else td.textContent = value;
      row.append(td);
    });
    const td = document.createElement('td'), button = document.createElement('button');
    button.className = 'text-button'; button.textContent = 'View matches ↗'; button.setAttribute('aria-label', `View matches for ${obj.name}`);
    button.onclick = () => { $('match-object').value = obj.id; setView('matches'); $('result-image').scrollIntoView({block:'center', behavior:'smooth'}); };
    td.append(button); row.append(td); $('result-rows').append(row);
  });
  setView('detection');
  if (!found) notice('No objects were confirmed. Inspect Matches or try a clearer scene and adjust the settings.');
}
$('run').onclick = async () => {
  if (busy) return;
  if (!$('min-inliers').reportValidity()) return;
  const file = $('upload').files[0];
  if (file && file.size > 20 * 1024 * 1024 - 2048) return notice('Please choose an image smaller than 20 MB.', true);
  const form = new FormData();
  form.append('scene', $('scene').value); form.append('ratio', $('ratio').value); form.append('min_inliers', $('min-inliers').value);
  if (file) form.append('image', file);
  setBusy(true); $('busy-overlay').hidden = false; $('run').textContent = 'Analyzing…';
  try { result = await api('/api/detect', {method:'POST', body:form}); renderResults(); }
  catch(error) { notice(error.message, true); }
  finally { setBusy(false); $('busy-overlay').hidden = true; $('run').textContent = 'Run detection ↗'; }
};
$('scene').onchange = sourceChanged; $('upload').onchange = sourceChanged;
$('clear-upload').onclick = () => { $('upload').value = ''; sourceChanged(); };
$('ratio').oninput = () => $('ratio-value').textContent = Number($('ratio').value).toFixed(2);
$('match-object').onchange = () => setView('matches');
document.querySelectorAll('[data-view]').forEach(button => button.onclick = () => {
  if (!result && button.dataset.view !== 'detection') return notice('Run detection to unlock the image views.');
  setView(button.dataset.view);
});
document.querySelectorAll('[data-page]').forEach(button => button.onclick = () => {
  document.querySelectorAll('.page').forEach(page => page.hidden = page.id !== `${button.dataset.page}-page`);
  document.querySelectorAll('[data-page]').forEach(nav => { nav.classList.toggle('active', nav === button); nav.setAttribute('aria-current', nav === button ? 'page' : 'false'); });
});
$('download-report').onclick = () => {
  if (!result) return;
  const {images, original, ...report} = result;
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = 'object-lab-report.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$('evaluate').onclick = async () => {
  if (!result) return;
  try {
    const metrics = await api('/api/evaluate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
      detected: result.objects.filter(obj => obj.detected).map(obj => obj.id),
      expected: [...document.querySelectorAll('#truth-options input:checked')].map(input => input.value)
    })});
    $('metrics').textContent = `Precision ${(metrics.precision * 100).toFixed(1)}% · Recall ${(metrics.recall * 100).toFixed(1)}% · F1 ${(metrics.f1 * 100).toFixed(1)}% · Accuracy ${(metrics.accuracy * 100).toFixed(1)}% | TP ${metrics.tp} / FP ${metrics.fp} / FN ${metrics.fn} / TN ${metrics.tn}`;
  } catch(error) { notice(error.message, true); }
};
$('stitch').onclick = async () => {
  if (busy) return;
  const scenes = [...document.querySelectorAll('#stitch-scenes input:checked')].map(input => input.value);
  if (scenes.length < 2 || scenes.length > 6) return notice('Choose between 2 and 6 overlapping scenes.', true);
  setBusy(true); $('stitch').textContent = 'Stitching scenes…'; $('panorama-result').hidden = true;
  try {
    const data = await api('/api/stitch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({scenes})});
    $('panorama-image').src = data.image; $('download-panorama').href = data.image; $('panorama-result').hidden = false;
  } catch(error) { notice(error.message, true); }
  finally { setBusy(false); $('stitch').textContent = 'Stitch selected scenes ↗'; }
};
async function init() {
  $('run').disabled = true;
  try {
    catalog = await api('/api/catalog');
    catalog.scenes.forEach(scene => {
      $('scene').add(new Option(scene.name, scene.id));
      const label = document.createElement('label'), img = document.createElement('img'), input = document.createElement('input');
      img.src = scene.url; img.alt = scene.name; img.loading = 'lazy'; input.type = 'checkbox'; input.value = scene.id;
      label.append(img, input, document.createTextNode(` ${scene.name}`)); $('stitch-scenes').append(label);
    });
    catalog.objects.forEach(obj => {
      $('match-object').add(new Option(obj.name, obj.id));
      const card = document.createElement('article'); card.className = 'panel object-card';
      const img = document.createElement('img'); img.src = obj.url; img.alt = obj.name; img.loading = 'lazy';
      const title = document.createElement('h2'); title.textContent = obj.name;
      const note = document.createElement('p'); note.textContent = `${obj.id}.png · Reference image`;
      card.append(img, title, note); $('object-grid').append(card);
      const label = document.createElement('label'), input = document.createElement('input'); input.type = 'checkbox'; input.value = obj.id;
      label.append(input, document.createTextNode(` ${obj.name}`)); $('truth-options').append(label);
    });
    sourceChanged(); $('run').disabled = false;
  } catch(error) { notice(`Could not load the project: ${error.message}. Reload the page to retry.`, true); }
}
init();
