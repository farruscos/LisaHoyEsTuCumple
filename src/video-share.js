const shareId = window.location.pathname.split('/').filter(Boolean).pop();
const statusBox = document.getElementById('sharedStatus');
const videoContainer = document.getElementById('sharedVideoContainer');
const videoPlayer = document.getElementById('sharedVideoPlayer');
const downloadBtn = document.getElementById('sharedDownloadBtn');
const shareContainer = document.getElementById('sharedShareContainer');
const nativeShareBtn = document.getElementById('sharedNativeShareBtn');
const copyShareBtn = document.getElementById('sharedCopyShareBtn');
const whatsappShareBtn = document.getElementById('sharedWhatsappShareBtn');
const xShareBtn = document.getElementById('sharedXShareBtn');
const facebookShareBtn = document.getElementById('sharedFacebookShareBtn');
const expiryText = document.getElementById('sharedExpiry');

let currentShareUrl = window.location.href;
const shareText = 'Mira este vídeo personalizado de cumpleaños.';

loadSharedVideo();

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

async function loadSharedVideo() {
    try {
        const response = await fetch(`/api/video/${shareId}`);

        if (!response.ok) {
            if (response.status === 410) {
                throw new Error('Este enlace ha caducado.');
            }
            throw new Error('No se pudo cargar el vídeo compartido.');
        }

        const payload = await response.json();
        currentShareUrl = payload.share_url;

        videoPlayer.src = payload.video_url;
        downloadBtn.href = `${payload.video_url}?download=1`;
        downloadBtn.download = 'cumple-personalizado.mp4';
        videoContainer.style.display = 'flex';

        configureShareButtons(payload.expires_at);
        showStatus('Vídeo listo para reproducir.', 'success');
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
