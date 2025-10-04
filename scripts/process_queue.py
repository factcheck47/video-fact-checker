import os
import json
from github import Github, Auth
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

def get_transcript(video_id):
    """Fetch transcript for a YouTube video."""
    try:
        # Create an instance and get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript_list
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        # Try with different language codes if English fails
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            return transcript.fetch()
        except Exception as e2:
            print(f"Error fetching transcript with fallback: {e2}")
            return None

def format_transcript(transcript):
    """Convert transcript to readable text with timestamps."""
    if not transcript:
        return None, None
    
    formatted = []
    for entry in transcript:
        formatted.append({
            'start': entry['start'],
            'text': entry['text']
        })
    
    full_text = ' '.join([entry['text'] for entry in transcript])
    return full_text, formatted

def fact_check_content(text, client):
    """Use OpenAI to fact-check the content."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a fact-checker. Analyze the provided transcript and identify claims that need fact-checking. For each claim, provide: the claim text, whether it's accurate/inaccurate/misleading/unverifiable, a brief explanation, and surrounding context from the transcript. Return as JSON array with format: [{\"claim\": \"text\", \"verdict\": \"accurate/inaccurate/misleading/unverifiable\", \"explanation\": \"brief explanation\", \"context\": \"surrounding context\"}]"},
                {"role": "user", "content": f"Fact-check this video transcript:\n\n{text[:15000]}"}
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        try:
            claims = json.loads(result)
            return claims
        except:
            return [{"claim": "Analysis completed", "verdict": "info", "explanation": result}]
            
    except Exception as e:
        print(f"Error fact-checking: {e}")
        return [{"claim": "Error", "verdict": "error", "explanation": str(e)}]

def match_claims_to_timestamps(claims, transcript_data):
    """Match fact-checked claims back to transcript timestamps."""
    results = []
    
    for claim in claims:
        claim_text = claim.get('claim', '').lower()
        context_text = claim.get('context', '').lower()
        
        best_match_time = 0
        
        for entry in transcript_data:
            entry_text = entry['text'].lower()
            
            if claim_text and any(word in entry_text for word in claim_text.split() if len(word) > 4):
                best_match_time = entry['start']
                break
            elif context_text and context_text[:50] in entry_text:
                best_match_time = entry['start']
                break
        
        results.append({
            'timestamp': best_match_time,
            'claim': claim.get('claim', ''),
            'verdict': claim.get('verdict', 'unverified'),
            'explanation': claim.get('explanation', '')
        })
    
    return results

def process_video(video_id, openai_client):
    """Process a single video fact-check."""
    print(f"Processing video: {video_id}")
    
    # Check if already processed
    output_path = f"results/{video_id}.json"
    if os.path.exists(output_path):
        print(f"Video {video_id} already processed, skipping")
        return True
    
    # Get transcript
    transcript = get_transcript(video_id)
    if not transcript:
        print("Failed to get transcript")
        return False
    
    # Format transcript
    full_text, transcript_data = format_transcript(transcript)
    print(f"Transcript length: {len(full_text)} characters")
    
    # Fact check
    claims = fact_check_content(full_text, openai_client)
    print(f"Found {len(claims)} claims to check")
    
    # Match to timestamps
    results = match_claims_to_timestamps(claims, transcript_data)
    
    # Save results
    os.makedirs("results", exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'video_id': video_id,
            'claims': results
        }, f, indent=2)
    
    print(f"Results saved to {output_path}")
    return True

def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    
    if not all([github_token, openai_api_key, repo_name]):
        print("Missing required environment variables")
        return
    
    # Initialize clients with new auth method
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)
    openai_client = OpenAI(api_key=openai_api_key)
    
    # Get all open issues
    issues = repo.get_issues(state='open')
    
    processed_count = 0
    
    for issue in issues:
        # Check if issue title starts with "Fact-check:"
        if not issue.title.startswith('Fact-check:'):
            continue
        
        # Extract video ID from title
        # Expected format: "Fact-check: VIDEO_ID"
        video_id = issue.title.replace('Fact-check:', '').strip()
        
        if not video_id:
            issue.create_comment("❌ Invalid format. Title should be: `Fact-check: VIDEO_ID`")
            issue.edit(state='closed')
            continue
        
        print(f"Processing issue #{issue.number} for video {video_id}")
        
        # Process the video
        success = process_video(video_id, openai_client)
        
        if success:
            # Close issue with success comment
            issue.create_comment(f"✅ Fact-check complete! View results at: https://{repo.owner.login}.github.io/{repo.name}/?v={video_id}")
            issue.edit(state='closed', labels=['completed'])
            processed_count += 1
        else:
            # Comment with error
            issue.create_comment("❌ Failed to process video. Please check the video ID and try again.")
            issue.edit(state='closed', labels=['failed'])
    
    print(f"Processed {processed_count} videos")

if __name__ == "__main__":
    main()
