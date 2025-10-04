const GITHUB_CONFIG = {
    owner: 'factcheck47',
    repo: 'video-fact-checker',
    // User will need to add their Personal Access Token here
    // Get it from: https://github.com/settings/tokens
    // Needs: repo scope (for repository_dispatch and reading/writing files)
    token: 'YOUR_GITHUB_PAT_HERE'
};

class GitHubAPI {
    constructor(config) {
        this.config = config;
        this.baseURL = 'https://api.github.com';
    }

    async triggerFactCheck(videoId) {
        const url = `${this.baseURL}/repos/${this.config.owner}/${this.config.repo}/dispatches`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `token ${this.config.token}`,
                    'Accept': 'application/vnd.github+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event_type: 'fact-check-video',
                    client_payload: {
                        video_id: videoId
                    }
                })
            });

            if (response.status === 204) {
                console.log('Workflow triggered successfully');
                return true;
            } else {
                console.error('Failed to trigger workflow:', response.status);
                return false;
            }
        } catch (error) {
            console.error('Error triggering workflow:', error);
            return false;
        }
    }

    async checkForResults(videoId) {
        const url = `${this.baseURL}/repos/${this.config.owner}/${this.config.repo}/contents/results/${videoId}.json`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Authorization': `token ${this.config.token}`,
                    'Accept': 'application/vnd.github+json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                // Content is base64 encoded
                const content = atob(data.content);
                return JSON.parse(content);
            } else if (response.status === 404) {
                // File doesn't exist yet
                return null;
            } else {
                console.error('Error checking results:', response.status);
                return null;
            }
        } catch (error) {
            console.error('Error fetching results:', error);
            return null;
        }
    }

    async pollForResults(videoId, maxAttempts = 30, interval = 5000) {
        // Poll every 5 seconds, up to 30 times (2.5 minutes)
        for (let i = 0; i < maxAttempts; i++) {
            console.log(`Polling attempt ${i + 1}/${maxAttempts}`);
            
            const results = await this.checkForResults(videoId);
            
            if (results) {
                console.log('Results found!');
                return results;
            }
            
            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, interval));
        }
        
        throw new Error('Timeout waiting for results');
    }
}

// Export for use in other files
const githubAPI = new GitHubAPI(GITHUB_CONFIG);
