const shareId = window.location.pathname.split('/').filter(Boolean).pop();
const statusBox = document.getElementById('sharedStatus');
const audioContainer = document.getElementById('sharedAudioContainer');
const audioPlayer = document.getElementById('sharedAudioPlayer');
const downloadBtn = document.getElementById('sharedDownloadBtn');
const shareContainer = document.getElementById('sharedShareContainer');
const nativeShareBtn = document.getElementById('sharedNativeShareBtn');
const copyShareBtn = document.getElementById('sharedCopyShareBtn');
const whatsappShareBtn = document.getElementById('sharedWhatsappShareBtn');
const xShareBtn = document.getElementById('sharedXShareBtn');
const facebookShareBtn = document.getElementById('sharedFacebookShareBtn');
const expiryText = document.getElementById('sharedExpiry');

let currentShareUrl = window.location.href;
const shareText = 'Escucha este audio personalizado de cumpleaños.';

loadSharedAudio();

nativeShareBtn.addEventListener('click', async () => {
    if (!navigator.share) {
        return;
    }

    try {
        await navigator.share({
            title: 'Lisa Hoy Es Tu Cumple',
            text: shareText,
            url: currentShareUrl,
        });
    } catch (error) {
        if (error.name !== 'AbortError') {
            showStatus('No se pudo abrir el panel de compartir.', 'error');
        }
    }
});

copyShareBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(currentShareUrl);
        showStatus('Enlace copiado al portapapeles.', 'success');
    } catch {
        showStatus('No se pudo copiar el enlace.', 'error');
    }
});

async function loadSharedAudio() {
    try {
        const response = await fetch(`/api/share/${shareId}`);

        if (!response.ok) {
            if (response.status === 410) {
                throw new Error('Este enlace ha caducado.');
            }
            throw new Error('No se pudo cargar el audio compartido.');
        }

        const payload = await response.json();
        currentShareUrl = payload.share_url;

        audioPlayer.src = payload.audio_url;
        downloadBtn.href = `${payload.audio_url}?download=1`;
        downloadBtn.download = 'cumple-personalizado.mp3';
        audioContainer.style.display = 'flex';

        configureShareButtons(payload.expires_at);
        showStatus('Audio listo para reproducir.', 'success');
    } catch (error) {
        showStatus(error.message, 'error');
    }
}

function configureShareButtons(expiresAt) {
    const encodedUrl = encodeURIComponent(currentShareUrl);
    const encodedText = encodeURIComponent(shareText);

    whatsappShareBtn.href = `https://wa.me/?text=${encodedText}%20${encodedUrl}`;
    xShareBtn.href = `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`;
    facebookShareBtn.href = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
    nativeShareBtn.style.display = navigator.share ? 'inline-flex' : 'none';
    expiryText.textContent = expiresAt ? `Disponible hasta ${formatDate(expiresAt)}.` : '';
    shareContainer.style.display = 'block';
}

function showStatus(message, type) {
    statusBox.textContent = message;
    statusBox.className = `status-message show ${type}`;
}

function formatDate(value) {
    return new Intl.DateTimeFormat('es-ES', {
        dateStyle: 'short',
        timeStyle: 'short',
    }).format(new Date(value));
}
