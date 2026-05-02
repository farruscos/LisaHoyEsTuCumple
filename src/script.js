const API_BASE_URL = '/api';

const form = document.getElementById('customizeForm');
const customNameInput = document.getElementById('customName');
const submitBtn = document.getElementById('submitBtn');
const statusMessage = document.getElementById('statusMessage');
const audioContainer = document.getElementById('audioContainer');
const audioPlayer = document.getElementById('audioPlayer');
const downloadBtn = document.getElementById('downloadBtn');
const noAudio = document.getElementById('noAudio');
const previewSection = document.querySelector('.preview-section');
const shareContainer = document.getElementById('shareContainer');
const nativeShareBtn = document.getElementById('nativeShareBtn');
const copyShareBtn = document.getElementById('copyShareBtn');
const whatsappShareBtn = document.getElementById('whatsappShareBtn');
const xShareBtn = document.getElementById('xShareBtn');
const facebookShareBtn = document.getElementById('facebookShareBtn');
const shareExpiry = document.getElementById('shareExpiry');

let currentAudioUrl = null;
let currentDownloadName = 'cumple-personalizado.mp3';
let currentShareUrl = null;
let currentShareText = '';

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const customName = customNameInput.value.trim();

    if (!customName) {
        showStatus('Introduce un nombre.', 'error');
        return;
    }

    submitBtn.disabled = true;
    setPreviewBusy(true);
    showStatus(`Generando el audio para "${customName}"...`, 'loading');

    try {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: customName }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'No se pudo generar el audio');
        }

        const contentType = response.headers.get('Content-Type') || '';

        if (contentType.includes('application/json')) {
            const payload = await response.json();
            loadGeneratedAudio({
                audioUrl: payload.audio_url,
                downloadUrl: payload.download_url || payload.audio_url,
                downloadName: payload.download_name || `cumple-${customName.toLowerCase()}.mp3`,
                shareUrl: payload.share_url,
                expiresAt: payload.expires_at,
                customName,
            });
        } else {
            const blob = await response.blob();

            if (currentAudioUrl && currentAudioUrl.startsWith('blob:')) {
                URL.revokeObjectURL(currentAudioUrl);
            }

            const audioUrl = URL.createObjectURL(blob);
            loadGeneratedAudio({
                audioUrl,
                downloadUrl: audioUrl,
                downloadName: `cumple-${customName.toLowerCase()}.mp3`,
                customName,
            });
        }

        showStatus(`Audio creado correctamente para "${customName}".`, 'success');
    } catch (error) {
        console.error('Error:', error);
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        setPreviewBusy(false);
    }
});

nativeShareBtn.addEventListener('click', async () => {
    if (!currentShareUrl || !navigator.share) {
        return;
    }

    try {
        await navigator.share({
            title: 'Lisa Hoy Es Tu Cumple',
            text: currentShareText,
            url: currentShareUrl,
        });
    } catch (error) {
        if (error.name !== 'AbortError') {
            showStatus('No se pudo abrir el panel de compartir.', 'error');
        }
    }
});

copyShareBtn.addEventListener('click', async () => {
    if (!currentShareUrl) {
        return;
    }

    try {
        await navigator.clipboard.writeText(currentShareUrl);
        showStatus('Enlace copiado al portapapeles.', 'success');
    } catch {
        showStatus('No se pudo copiar el enlace.', 'error');
    }
});

function loadGeneratedAudio({ audioUrl, downloadUrl, downloadName, shareUrl, expiresAt, customName }) {
    if (currentAudioUrl && currentAudioUrl.startsWith('blob:') && currentAudioUrl !== audioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
    }

    currentAudioUrl = audioUrl;
    currentDownloadName = downloadName;
    currentShareUrl = shareUrl || null;
    currentShareText = `Escucha mi audio personalizado de cumpleaños para ${customName}.`;

    audioPlayer.src = currentAudioUrl;
    audioContainer.style.display = 'flex';
    noAudio.style.display = 'none';

    downloadBtn.href = downloadUrl;
    downloadBtn.download = currentDownloadName;

    updateShareControls(expiresAt);
}

function updateShareControls(expiresAt) {
    if (!currentShareUrl) {
        shareContainer.style.display = 'none';
        return;
    }

    const encodedUrl = encodeURIComponent(currentShareUrl);
    const encodedText = encodeURIComponent(currentShareText);

    whatsappShareBtn.href = `https://wa.me/?text=${encodedText}%20${encodedUrl}`;
    xShareBtn.href = `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`;
    facebookShareBtn.href = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
    nativeShareBtn.style.display = navigator.share ? 'inline-flex' : 'none';
    shareExpiry.textContent = expiresAt ? `El enlace estará disponible hasta ${formatDate(expiresAt)}.` : '';
    shareContainer.style.display = 'block';
}

function setPreviewBusy(isBusy) {
    previewSection.classList.toggle('is-busy', isBusy);
    previewSection.setAttribute('aria-busy', String(isBusy));

    if (isBusy) {
        audioPlayer.pause();
        audioPlayer.removeAttribute('controls');
        audioPlayer.removeAttribute('src');
        audioPlayer.load();
        downloadBtn.removeAttribute('href');
        downloadBtn.setAttribute('aria-disabled', 'true');
        downloadBtn.setAttribute('tabindex', '-1');
        shareContainer.classList.add('is-disabled');
    } else {
        audioPlayer.setAttribute('controls', '');

        if (currentAudioUrl && !audioPlayer.getAttribute('src')) {
            audioPlayer.src = currentAudioUrl;
            audioPlayer.load();
        }

        if (currentAudioUrl) {
            downloadBtn.href = currentAudioUrl;
            downloadBtn.download = currentDownloadName;
        }

        downloadBtn.removeAttribute('aria-disabled');
        downloadBtn.removeAttribute('tabindex');
        shareContainer.classList.remove('is-disabled');
    }
}

function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message show ${type}`;

    if (type === 'success') {
        setTimeout(() => {
            statusMessage.classList.remove('show');
        }, 5000);
    }
}

function formatDate(value) {
    return new Intl.DateTimeFormat('es-ES', {
        dateStyle: 'short',
        timeStyle: 'short',
    }).format(new Date(value));
}

noAudio.style.display = 'block';
audioContainer.style.display = 'none';
shareContainer.style.display = 'none';
