const audio = document.getElementById('audio-engine');
const player = document.getElementById('mini-player');
let currentFileId = null;
let saveTimer = null;

async function playAudio(fileId, title, subtitle, thumbUrl) {
  // Fetch signed CloudFront URL from backend
  const resp = await fetch(`/api/play/${fileId}`, {method: 'POST'});
  if (resp.status === 401) { window.location.href = '/login'; return; }
  if (!resp.ok) { alert('ఆడియో లోడ్ చేయడంలో వైఫల్యం'); return; }
  const { url } = await resp.json();

  currentFileId = fileId;
  audio.src = url;
  audio.play();

  // Update player UI
  document.getElementById('player-title').textContent = title;
  document.getElementById('player-subtitle').textContent = subtitle;
  document.getElementById('player-thumb').src = thumbUrl || '/static/icons/default-thumb.png';
  document.getElementById('btn-play-pause').textContent = '⏸';
  player.classList.remove('hidden');

  // Restore saved position if any
  const saved = sessionStorage.getItem(`pos_${fileId}`);
  if (saved && parseFloat(saved) > 5) {
    audio.currentTime = parseFloat(saved);
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

  // Save position every 5 seconds
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
    // best-effort; ignore network failures
  }
}

// Save position when user navigates away
window.addEventListener('beforeunload', savePositionToServer);

// Register PWA service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}
