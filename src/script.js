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

let currentAudioUrl = null;
let currentDownloadName = 'customized-audio.mp3';

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const customName = customNameInput.value.trim();

    if (!customName) {
        showStatus('Please enter a name.', 'error');
        return;
    }

    submitBtn.disabled = true;
    setPreviewBusy(true);
    showStatus(`Creating custom audio with "${customName}"...`, 'loading');

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
            throw new Error(error.error || 'Failed to generate audio');
        }

        const blob = await response.blob();

        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
        }

        currentAudioUrl = URL.createObjectURL(blob);
        currentDownloadName = `customized-${customName.toLowerCase()}.mp3`;
        audioPlayer.src = currentAudioUrl;
        audioContainer.style.display = 'flex';
        noAudio.style.display = 'none';

        downloadBtn.href = currentAudioUrl;
        downloadBtn.download = currentDownloadName;

        showStatus(`Audio created successfully. Now playing with "${customName}".`, 'success');
    } catch (error) {
        console.error('Error:', error);
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        setPreviewBusy(false);
    }
});

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

noAudio.style.display = 'block';
audioContainer.style.display = 'none';
