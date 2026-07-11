const audio = document.getElementById('audio-engine');
const player = document.getElementById('mini-player');
let currentFileId = null;
let saveTimer = null;

async function playAudio(fileId, title, subtitle, thumbUrl) {
  const resp = await fetch(`/api/play/${fileId}`, {method: 'POST'});
  if (resp.status === 401) { window.location.href = '/login'; return; }
  if (resp.status === 503) { alert('ఆడియో స్ట్రీమింగ్ త్వరలో అందుబాటులో ఉంటుంది (AWS సెటప్ పెండింగ్)'); return; }
  if (!resp.ok) { alert('ఆడియో లోడ్ చేయడంలో వైఫల్యం'); return; }
  const { url } = await resp.json();

  currentFileId = fileId;
  audio.src = url;
  audio.play();

  // Update mini-player UI
  document.getElementById('player-title').textContent = title;
  document.getElementById('player-subtitle').textContent = subtitle;
  document.getElementById('player-thumb').src = thumbUrl || '/static/icons/default-thumb.png';
  document.getElementById('btn-play-pause').textContent = '⏸';
  player.classList.remove('hidden');

  // Highlight active chapter row, remove from others
  document.querySelectorAll('.episode-row').forEach(row => row.classList.remove('ep-active'));
  const activeRow = document.getElementById(`ep-${fileId}`);
  if (activeRow) activeRow.classList.add('ep-active');

  // Restore saved position if any
  const saved = sessionStorage.getItem(`pos_${fileId}`);
  if (saved && parseFloat(saved) > 5) {
    audio.currentTime = parseFloat(saved);
  }
}

function playNextChapter() {
  const chapters = window.chapterList;
  if (!chapters || !currentFileId) return;
  const idx = chapters.findIndex(c => c.id === currentFileId);
  if (idx !== -1 && idx < chapters.length - 1) {
    const next = chapters[idx + 1];
    playAudio(next.id, next.title, next.subtitle, next.thumb);
  }
}

function togglePlay() {
  if (audio.paused) {
    audio.play();
    document.getElementById('btn-play-pause').textContent = '⏸';
  } else {
    audio.pause();
    document.getElementById('btn-play-pause').textContent = '▶';
  }
}

function seekBy(seconds) {
  audio.currentTime = Math.max(0, audio.currentTime + seconds);
}

function seekTo(value) {
  if (audio.duration) audio.currentTime = (value / 100) * audio.duration;
}

function setSpeed(value) {
  audio.playbackRate = parseFloat(value);
}

function closePlayer() {
  audio.pause();
  player.classList.add('hidden');
  document.querySelectorAll('.episode-row').forEach(row => row.classList.remove('ep-active'));
  currentFileId = null;
}

function formatTime(sec) {
  if (!sec || isNaN(sec)) return '0:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

audio.addEventListener('timeupdate', () => {
  const seek = document.getElementById('player-seek');
  const cur = document.getElementById('player-current');
  if (audio.duration) {
    seek.value = (audio.currentTime / audio.duration) * 100;
  }
  cur.textContent = formatTime(audio.currentTime);

  if (currentFileId) {
    sessionStorage.setItem(`pos_${currentFileId}`, audio.currentTime);
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => savePositionToServer(), 5000);
  }
});

audio.addEventListener('loadedmetadata', () => {
  document.getElementById('player-duration').textContent = formatTime(audio.duration);
});

audio.addEventListener('ended', () => {
  document.getElementById('btn-play-pause').textContent = '▶';
  savePositionToServer();
  // Auto-play next chapter after 1 second pause
  setTimeout(playNextChapter, 1000);
});

audio.addEventListener('pause', () => {
  document.getElementById('btn-play-pause').textContent = '▶';
});

audio.addEventListener('play', () => {
  document.getElementById('btn-play-pause').textContent = '⏸';
});

async function savePositionToServer() {
  if (!currentFileId || !audio.currentTime) return;
  try {
    await fetch('/api/position', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        audio_file_id: currentFileId,
        position_sec: Math.floor(audio.currentTime),
      }),
    });
  } catch (_) {
    // best-effort
  }
}

window.addEventListener('beforeunload', savePositionToServer);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}
