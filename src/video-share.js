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
const brandTitleBox = document.getElementById('sharedBrandTitle');
const titleBox = document.getElementById('sharedTitle');
const descriptionBox = document.getElementById('sharedDescription');

let currentShareUrl = window.location.href;
let shareTitle = document.title || 'Lisa Hoy Es Tu Cumple';
let shareText = descriptionBox?.textContent || 'Mira este vídeo personalizado de cumpleaños.';

loadSharedVideo();

nativeShareBtn.addEventListener('click', async () => {
    if (!navigator.share) {
        return;
    }

    try {
        await navigator.share({
            title: shareTitle,
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

        updateShareCopy(payload.custom_name);

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

function updateShareCopy(customName) {
    if (!customName) {
        return;
    }

    const brandTitle = `${customName} Hoy Es Tu Cumple`;
    shareTitle = brandTitle;
    shareText = `Han creado este vídeo personalizado de cumpleaños para ${customName}.`;
    document.title = shareTitle;

    if (brandTitleBox) {
        brandTitleBox.textContent = brandTitle;
    }

    if (titleBox) {
        titleBox.textContent = `Vídeo para ${customName}`;
    }

    if (descriptionBox) {
        descriptionBox.textContent = shareText;
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
