import os
import json
import sys
import re
from github import Github, Auth
from openai import OpenAI

def extract_transcript_from_issue(issue_body):
    """Extract transcript JSON from issue body."""
    try:
        # Look for JSON code block in the issue body
        json_match = re.search(r'```json\n(.*?)\n```', issue_body, re.DOTALL)
        
        if not json_match:
            print("No JSON transcript found in issue body")
            return None
        
        transcript_json = json_match.group(1)
        transcript = json.loads(transcript_json)
        
        print(f"Extracted transcript with {len(transcript)} entries from issue")
        return transcript
        
    except Exception as e:
        print(f"Error extracting transcript from issue: {e}")
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

def process_video(video_id, transcript, openai_client):
    """Process a single video fact-check using provided transcript."""
    print(f"Processing video: {video_id}")
    
    # Check if already processed
    output_path = f"results/{video_id}.json"
    if os.path.exists(output_path):
        print(f"Video {video_id} already processed, skipping")
        return {'success': True, 'message': 'Already processed'}
    
    # Validate transcript
    if not transcript:
        raise Exception("No transcript provided")
    
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
    return {'success': True, 'message': 'Fact-check completed successfully'}

def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    issue_number = os.environ.get('ISSUE_NUMBER')
    
    if not all([github_token, openai_api_key, repo_name, issue_number]):
        print("Missing required environment variables")
        sys.exit(1)
    
    # Initialize clients
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)
    openai_client = OpenAI(api_key=openai_api_key)
    
    # Get the specific issue
    issue = repo.get_issue(int(issue_number))
    
    # Extract video ID from title
    video_id = issue.title.replace('Fact-check:', '').strip()
    
    if not video_id:
        issue.create_comment("❌ Invalid format. Title should be: `Fact-check: VIDEO_ID`")
        issue.edit(state='closed', labels=['failed'])
        sys.exit(1)
    
    print(f"Processing issue #{issue.number} for video {video_id}")
    
    # Extract transcript from issue body
    transcript = extract_transcript_from_issue(issue.body or '')
    
    if not transcript:
        error_msg = "No transcript found in issue. Please use the web app to create issues with transcripts."
        issue.create_comment(f"❌ {error_msg}")
        issue.edit(state='closed', labels=['failed'])
        sys.exit(1)
    
    # Process the video
    try:
        result = process_video(video_id, transcript, openai_client)
        
        # Close issue with success comment
        issue.create_comment(f"✅ Fact-check complete! {result['message']}\n\nView results at: https://{repo.owner.login}.github.io/{repo.name}/?v={video_id}")
        issue.edit(state='closed', labels=['completed'])
        
        print(f"✅ Successfully processed video {video_id}")
        
    except Exception as e:
        # Comment with detailed error and close issue
        error_msg = str(e)
        issue.create_comment(f"❌ Failed to process video.\n\n**Error:** {error_msg}\n\n**Possible solutions:**\n- Make sure the transcript was included in the issue\n- Try creating a new issue using the web app")
        issue.edit(state='closed', labels=['failed'])
        
        print(f"❌ Failed to process video {video_id}: {error_msg}")
        sys.exit(1)

if __name__ == "__main__":
    main()
