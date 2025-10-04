class VideoPlayer {
    constructor() {
        this.player = null;
        this.claims = [];
        this.activeBubbles = new Set();
        this.checkInterval = null;
    }

    loadYouTubeAPI() {
        return new Promise((resolve) => {
            if (window.YT && window.YT.Player) {
                resolve();
                return;
            }

            window.onYouTubeIframeAPIReady = resolve;
            
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        });
    }

    async initialize(videoId, claimsData) {
        this.claims = claimsData;
        
        await this.loadYouTubeAPI();
        
        return new Promise((resolve) => {
            this.player = new YT.Player('player', {
                videoId: videoId,
                width: '100%',
                height: '100%',
                playerVars: {
                    autoplay: 0,
                    rel: 0
                },
                events: {
                    onReady: () => {
                        this.startOverlayCheck();
                        resolve();
                    },
                    onStateChange: (event) => {
                        if (event.data === YT.PlayerState.PLAYING) {
                            this.startOverlayCheck();
                        } else {
                            this.stopOverlayCheck();
                        }
                    }
                }
            });
        });
    }

    startOverlayCheck() {
        if (this.checkInterval) return;
        
        this.checkInterval = setInterval(() => {
            this.updateOverlays();
        }, 500); // Check every 500ms
    }

    stopOverlayCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }

    updateOverlays() {
        if (!this.player || !this.player.getCurrentTime) return;
        
        const currentTime = this.player.getCurrentTime();
        const overlaysContainer = document.getElementById('overlays');
        
        // Show/hide bubbles based on timestamp
        this.claims.forEach((claim, index) => {
            const shouldShow = Math.abs(currentTime - claim.timestamp) < 3; // Show within 3 seconds
            const bubbleId = `bubble-${index}`;
            
            if (shouldShow && !this.activeBubbles.has(bubbleId)) {
                this.showBubble(claim, index, overlaysContainer);
                this.activeBubbles.add(bubbleId);
            } else if (!shouldShow && this.activeBubbles.has(bubbleId)) {
                this.hideBubble(bubbleId);
                this.activeBubbles.delete(bubbleId);
            }
        });
    }

    showBubble(claim, index, container) {
        const bubble = document.createElement('div');
        bubble.id = `bubble-${index}`;
        bubble.className = `fact-bubble ${claim.verdict}`;
        
        // Random position (you can make this smarter based on video content)
        const top = 20 + (index * 15) % 60;
        const left = 10 + (index * 20) % 70;
        
        bubble.style.top = `${top}%`;
        bubble.style.left = `${left}%`;
        
        bubble.innerHTML = `
            <strong>${claim.verdict.toUpperCase()}</strong><br>
            ${claim.explanation.substring(0, 100)}${claim.explanation.length > 100 ? '...' : ''}
        `;
        
        bubble.onclick = () => this.seekToTime(claim.timestamp);
        
        container.appendChild(bubble);
    }

    hideBubble(bubbleId) {
        const bubble = document.getElementById(bubbleId);
        if (bubble) {
            bubble.remove();
        }
    }

    seekToTime(timestamp) {
        if (this.player && this.player.seekTo) {
            this.player.seekTo(timestamp, true);
            this.player.playVideo();
        }
    }

    renderClaimsList(claims) {
        const claimsList = document.getElementById('claimsList');
        claimsList.innerHTML = '';
        
        claims.forEach((claim, index) => {
            const claimItem = document.createElement('div');
            claimItem.className = `claim-item ${claim.verdict}`;
            claimItem.onclick = () => this.seekToTime(claim.timestamp);
            
            const minutes = Math.floor(claim.timestamp / 60);
            const seconds = Math.floor(claim.timestamp % 60);
            const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            claimItem.innerHTML = `
                <div class="claim-verdict">${claim.verdict} @ ${timeStr}</div>
                <div class="claim-text">${claim.claim}</div>
                <div class="claim-explanation">${claim.explanation}</div>
            `;
            
            claimsList.appendChild(claimItem);
        });
    }

    destroy() {
        this.stopOverlayCheck();
        if (this.player && this.player.destroy) {
            this.player.destroy();
        }
        this.player = null;
        this.claims = [];
        this.activeBubbles.clear();
    }
}

const videoPlayer = new VideoPlayer();
