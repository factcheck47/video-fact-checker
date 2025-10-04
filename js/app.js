class FactCheckApp {
    constructor() {
        this.currentVideoId = null;
        this.init();
    }

    init() {
        const checkBtn = document.getElementById('checkBtn');
        const videoUrl = document.getElementById('videoUrl');

        checkBtn.addEventListener('click', () => this.handleCheck());
        
        videoUrl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleCheck();
            }
        });
    }

    extractVideoId(url) {
        // Handle various YouTube URL formats
        const patterns = [
            /(?:youtube\.com\/watch\?v=)([^&]+)/,
            /(?:youtu\.be\/)([^?]+)/,
            /(?:youtube\.com\/embed\/)([^?]+)/
        ];

        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match && match[1]) {
                return match[1];
            }
        }

        return null;
    }

    showStatus(message, type = 'info') {
        const status = document.getElementById('status');
        status.textContent = message;
        status.className = `status ${type}`;
        status.style.display = 'block';
    }

    hideStatus() {
        const status = document.getElementById('status');
        status.style.display = 'none';
    }

    async handleCheck() {
        const videoUrlInput = document.getElementById('videoUrl');
        const checkBtn = document.getElementById('checkBtn');
        const url = videoUrlInput.value.trim();

        if (!url) {
            this.showStatus('Please enter a YouTube URL', 'error');
            return;
        }

        const videoId = this.extractVideoId(url);
        
        if (!videoId) {
            this.showStatus('Invalid YouTube URL', 'error');
            return;
        }

        this.currentVideoId = videoId;

        // Disable input while processing
        checkBtn.disabled = true;
        videoUrlInput.disabled = true;

        try {
            // First check if results already exist
            this.showStatus('Checking for cached results...', 'info');
            let results = await githubAPI.checkForResults(videoId);

            if (!results) {
                // No cached results, trigger workflow
                this.showStatus('No cached results found. Starting fact-check process...', 'info');
                
                const triggered = await githubAPI.triggerFactCheck(videoId);
                
                if (!triggered) {
                    throw new Error('Failed to trigger fact-check workflow');
                }

                this.showStatus('Fact-checking in progress... This may take 1-2 minutes', 'info');
                
                // Poll for results
                results = await githubAPI.pollForResults(videoId);
            }

            // Display results
            this.showStatus('Fact-check complete!', 'success');
            await this.displayResults(videoId, results.claims);

        } catch (error) {
            console.error('Error:', error);
            this.showStatus(`Error: ${error.message}`, 'error');
        } finally {
            checkBtn.disabled = false;
            videoUrlInput.disabled = false;
        }
    }

    async displayResults(videoId, claims) {
        const videoContainer = document.getElementById('videoContainer');
        videoContainer.classList.remove('hidden');

        // Destroy previous player if exists
        videoPlayer.destroy();

        // Initialize new player
        await videoPlayer.initialize(videoId, claims);
        
        // Render claims list
        videoPlayer.renderClaimsList(claims);

        // Scroll to video
        videoContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new FactCheckApp();
    });
} else {
    new FactCheckApp();
}
