const GITHUB_CONFIG = {
    owner: 'factcheck47',
    repo: 'video-fact-checker'
};

class GitHubAPI {
    constructor(config) {
        this.config = config;
        this.baseURL = 'https://api.github.com';
    }

    getIssueURL(videoId) {
        // Generate URL for creating a new issue with pre-filled title
        const title = encodeURIComponent(`Fact-check: ${videoId}`);
        const body = encodeURIComponent(`Please fact-check this video: https://youtube.com/watch?v=${videoId}`);
        return `https://github.com/${this.config.owner}/${this.config.repo}/issues/new?title=${title}&body=${body}`;
    }

    async checkForResults(videoId) {
        // No authentication needed to read from public repo
        const url = `https://raw.githubusercontent.com/${this.config.owner}/${this.config.repo}/main/results/${videoId}.json`;
        
        try {
            const response = await fetch(url);

            if (response.ok) {
                const data = await response.json();
                return data;
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

    async pollForResults(videoId, maxAttempts = 60, interval = 5000) {
        // Poll every 5 seconds, up to 60 times (5 minutes)
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
        
        throw new Error('Timeout waiting for results. The workflow runs every 5 minutes, so please wait and try again.');
    }
}

// Export for use in other files
const githubAPI = new GitHubAPI(GITHUB_CONFIG);
