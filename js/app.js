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

    showStatus(message, type = 'info', isHTML = false) {
        const status = document.getElementById('status');
        
        if (isHTML) {
            status.innerHTML = message;
        } else {
            status.textContent = message;
        }
        
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
                // No cached results, show instructions
                const issueUrl = githubAPI.getIssueURL(videoId);
                
                this.showStatus(
                    `No cached results found. To fact-check this video:<br><br>` +
                    `1. <a href="${issueUrl}" target="_blank" style="color: white; text-decoration: underline;">Click here to create a GitHub issue</a><br>` +
                    `2. Submit the issue (it will be pre-filled)<br>` +
                    `3. Come back here and click "Start Polling" below<br><br>` +
                    `<button id="startPolling" style="padding: 10px 20px; background: #48bb78; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; margin-top: 10px;">Start Polling for Results</button>`,
                    'info',
                    true
                );

                // Wait for user to click the polling button
                return new Promise((resolve) => {
                    const pollBtn = document.getElementById('startPolling');
                    pollBtn.onclick = async () => {
                        pollBtn.disabled = true;
                        pollBtn.textContent = 'Polling...';
                        
                        this.showStatus('Waiting for fact-check to complete... (this may take up to 5 minutes)', 'info');
                        
                        try {
                            results = await githubAPI.pollForResults(videoId, 60, 5000);
                            await this.displayResults(videoId, results.claims);
                            this.showStatus('Fact-check complete!', 'success');
                        } catch (error) {
                            this.showStatus(`Error: ${error.message}`, 'error');
                        }
                        
                        resolve();
                    };
                });
            }

            // Display results
            if (results) {
                this.showStatus('Fact-check complete!', 'success');
                await this.displayResults(videoId, results.claims);
            }

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
