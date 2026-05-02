const API_BASE_URL = '/api';

const form = document.getElementById('customizeForm');
const customNameInput = document.getElementById('customName');
const photoInput = document.getElementById('photoInput');
const photoPreview = document.getElementById('photoPreview');
const photoPreviewImage = document.getElementById('photoPreviewImage');
const clearPhotoBtn = document.getElementById('clearPhotoBtn');
const submitBtn = document.getElementById('submitBtn');
const statusMessage = document.getElementById('statusMessage');
const videoContainer = document.getElementById('videoContainer');
const videoPlayer = document.getElementById('videoPlayer');
const downloadBtn = document.getElementById('downloadBtn');
const noVideo = document.getElementById('noVideo');
const previewSection = document.querySelector('.preview-section');
const shareContainer = document.getElementById('shareContainer');
const nativeShareBtn = document.getElementById('nativeShareBtn');
const copyShareBtn = document.getElementById('copyShareBtn');
const whatsappShareBtn = document.getElementById('whatsappShareBtn');
const xShareBtn = document.getElementById('xShareBtn');
const facebookShareBtn = document.getElementById('facebookShareBtn');
const shareExpiry = document.getElementById('shareExpiry');

let currentVideoUrl = null;
let currentDownloadUrl = null;
let currentDownloadName = 'cumple-personalizado.mp4';
let currentShareUrl = null;
let currentShareText = '';
let currentPhotoPreviewUrl = null;

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const customName = customNameInput.value.trim();

    if (!customName) {
        showStatus('Introduce un nombre.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('name', customName);

    const hasPhoto = photoInput.files.length > 0;

    if (hasPhoto) {
        formData.append('photo', photoInput.files[0]);
    }

    submitBtn.disabled = true;
    photoInput.disabled = true;
    setPreviewBusy(true);
    showStatus(
        hasPhoto
            ? `Generando el vídeo para "${customName}". La foto tarda un poco más; deja esta pestaña abierta.`
            : `Generando el vídeo para "${customName}". Puede tardar unos segundos.`,
        'loading'
    );

    try {
        const response = await fetch(`${API_BASE_URL}/generate-video`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'No se pudo generar el vídeo');
        }

        const contentType = response.headers.get('Content-Type') || '';

        if (contentType.includes('application/json')) {
            const payload = await response.json();
            loadGeneratedVideo({
                videoUrl: payload.video_url,
                downloadUrl: payload.download_url || payload.video_url,
                downloadName: payload.download_name || `cumple-${slugify(customName)}.mp4`,
                shareUrl: payload.share_url,
                expiresAt: payload.expires_at,
                customName,
            });
        } else {
            const blob = await response.blob();

            if (currentVideoUrl && currentVideoUrl.startsWith('blob:')) {
                URL.revokeObjectURL(currentVideoUrl);
            }

            const videoUrl = URL.createObjectURL(blob);
            loadGeneratedVideo({
                videoUrl,
                downloadUrl: videoUrl,
                downloadName: `cumple-${slugify(customName)}.mp4`,
                customName,
            });
        }

        showStatus(`Vídeo creado correctamente para "${customName}".`, 'success');
    } catch (error) {
        console.error('Error:', error);
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        photoInput.disabled = false;
        setPreviewBusy(false);
    }
});

photoInput.addEventListener('change', () => {
    if (currentPhotoPreviewUrl) {
        URL.revokeObjectURL(currentPhotoPreviewUrl);
        currentPhotoPreviewUrl = null;
    }

    if (photoInput.files.length === 0) {
        photoPreview.style.display = 'none';
        photoPreviewImage.removeAttribute('src');
        return;
    }

    currentPhotoPreviewUrl = URL.createObjectURL(photoInput.files[0]);
    photoPreviewImage.src = currentPhotoPreviewUrl;
    photoPreview.style.display = 'flex';
});

clearPhotoBtn.addEventListener('click', () => {
    photoInput.value = '';
    photoInput.dispatchEvent(new Event('change'));
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

function loadGeneratedVideo({ videoUrl, downloadUrl, downloadName, shareUrl, expiresAt, customName }) {
    if (currentVideoUrl && currentVideoUrl.startsWith('blob:') && currentVideoUrl !== videoUrl) {
        URL.revokeObjectURL(currentVideoUrl);
    }

    currentVideoUrl = videoUrl;
    currentDownloadUrl = downloadUrl || videoUrl;
    currentDownloadName = downloadName;
    currentShareUrl = shareUrl || null;
    currentShareText = `Mira mi vídeo personalizado de cumpleaños para ${customName}.`;

    videoPlayer.src = currentVideoUrl;
    videoContainer.style.display = 'flex';
    noVideo.style.display = 'none';

    downloadBtn.href = currentDownloadUrl;
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
        videoPlayer.pause();
        videoPlayer.removeAttribute('controls');
        videoPlayer.removeAttribute('src');
        videoPlayer.load();
        downloadBtn.removeAttribute('href');
        downloadBtn.setAttribute('aria-disabled', 'true');
        downloadBtn.setAttribute('tabindex', '-1');
        shareContainer.classList.add('is-disabled');
    } else {
        videoPlayer.setAttribute('controls', '');

        if (currentVideoUrl && !videoPlayer.getAttribute('src')) {
            videoPlayer.src = currentVideoUrl;
            videoPlayer.load();
        }

        if (currentDownloadUrl) {
            downloadBtn.href = currentDownloadUrl;
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

function slugify(value) {
    return value
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'personalizado';
}

noVideo.style.display = 'block';
videoContainer.style.display = 'none';
shareContainer.style.display = 'none';
