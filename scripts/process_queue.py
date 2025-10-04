import os
import json
import sys
from github import Github, Auth
from openai import OpenAI
import yt_dlp

def get_transcript(video_id):
    """Fetch transcript for a YouTube video using yt-dlp."""
    try:
        url = f'https://www.youtube.com/watch?v={video_id}'
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'json3',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Try to get subtitles
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            # Prefer manual subtitles, fall back to auto-generated
            subtitle_data = None
            if 'en' in subtitles:
                subtitle_data = subtitles['en']
            elif 'en' in automatic_captions:
                subtitle_data = automatic_captions['en']
            
            if not subtitle_data:
                print("No English subtitles found")
                return None
            
            # Find json3 format
            json3_url = None
            for sub in subtitle_data:
                if sub.get('ext') == 'json3':
                    json3_url = sub.get('url')
                    break
            
            if not json3_url:
                print("No json3 subtitle format found")
                return None
            
            # Download and parse the subtitle data
            import urllib.request
            with urllib.request.urlopen(json3_url) as response:
                subtitle_json = json.loads(response.read().decode('utf-8'))
            
            # Convert to transcript format
            transcript = []
            events = subtitle_json.get('events', [])
            
            for event in events:
                if 'segs' in event:
                    start_time = event.get('tStartMs', 0) / 1000.0  # Convert to seconds
                    text = ''.join([seg.get('utf8', '') for seg in event['segs']])
                    if text.strip():
                        transcript.append({
                            'start': start_time,
                            'text': text.strip()
                        })
            
            print(f"Successfully fetched transcript with {len(transcript)} entries")
            return transcript
            
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        print(f"Error type: {type(e).__name__}")
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
        raise

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
    """Process a single video fact-check. Raises exceptions on failure."""
    print(f"Processing video: {video_id}")
    
    # Check if already processed
    output_path = f"results/{video_id}.json"
    if os.path.exists(output_path):
        print(f"Video {video_id} already processed, skipping")
        return {'success': True, 'message': 'Already processed'}
    
    # Get transcript - raise exception if fails
    transcript = get_transcript(video_id)
    if not transcript:
        raise Exception("Failed to get transcript. This video may have subtitles disabled or be unavailable.")
    
    # Format transcript
    full_text, transcript_data = format_transcript(transcript)
    print(f"Transcript length: {len(full_text)} characters")
    
    # Fact check - let exceptions bubble up
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
    return {'success': True, 'message': 'Fact-check completed successfully'}

def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    
    if not all([github_token, openai_api_key, repo_name]):
        print("Missing required environment variables")
        sys.exit(1)
    
    # Initialize clients with new auth method
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)
    openai_client = OpenAI(api_key=openai_api_key)
    
    # Get all open issues
    issues = repo.get_issues(state='open')
    
    processed_count = 0
    failed_count = 0
    
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
        
        # Process the video - let exceptions propagate
        try:
            result = process_video(video_id, openai_client)
            
            # Close issue with success comment
            issue.create_comment(f"✅ Fact-check complete! {result['message']}\n\nView results at: https://{repo.owner.login}.github.io/{repo.name}/?v={video_id}")
            issue.edit(state='closed', labels=['completed'])
            processed_count += 1
            
        except Exception as e:
            # Comment with detailed error and close issue
            error_msg = str(e)
            issue.create_comment(f"❌ Failed to process video.\n\n**Error:** {error_msg}\n\n**Possible solutions:**\n- Make sure the video has captions/subtitles enabled\n- Try a different video\n- Check that the video ID is correct: `{video_id}`")
            issue.edit(state='closed', labels=['failed'])
            failed_count += 1
            print(f"Failed to process video {video_id}: {error_msg}")
            
            # FAIL THE WORKFLOW - don't continue processing
            print(f"\n❌ WORKFLOW FAILED: Unable to process video {video_id}")
            print(f"Error: {error_msg}")
            sys.exit(1)
    
    print(f"\nProcessed {processed_count} videos successfully")
    
    if failed_count > 0:
        print(f"Failed {failed_count} videos")
        sys.exit(1)  # Exit with error if any videos failed
    
    if processed_count == 0:
        print("No videos to process")
        # This is not an error - just nothing to do
        sys.exit(0)

if __name__ == "__main__":
    main()
