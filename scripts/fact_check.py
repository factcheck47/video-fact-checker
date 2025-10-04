import os
import json
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

def get_transcript(video_id):
    """Fetch transcript for a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def format_transcript(transcript):
    """Convert transcript to readable text with timestamps."""
    if not transcript:
        return None
    
    formatted = []
    for entry in transcript:
        formatted.append({
            'start': entry['start'],
            'text': entry['text']
        })
    
    # Combine into full text for fact-checking
    full_text = ' '.join([entry['text'] for entry in transcript])
    return full_text, formatted

def fact_check_content(text, client):
    """Use OpenAI to fact-check the content."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a fact-checker. Analyze the provided transcript and identify claims that need fact-checking. For each claim, provide: the claim text, whether it's accurate/inaccurate/misleading/unverifiable, a brief explanation, and an approximate timestamp reference if you can infer it from context. Return as JSON array with format: [{\"claim\": \"text\", \"verdict\": \"accurate/inaccurate/misleading/unverifiable\", \"explanation\": \"brief explanation\", \"context\": \"surrounding context from transcript\"}]"},
                {"role": "user", "content": f"Fact-check this video transcript:\n\n{text[:15000]}"}  # Limit to avoid token limits
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        # Try to parse as JSON
        try:
            claims = json.loads(result)
            return claims
        except:
            # If not valid JSON, wrap in structure
            return [{"claim": "Analysis completed", "verdict": "info", "explanation": result}]
            
    except Exception as e:
        print(f"Error fact-checking: {e}")
        return [{"claim": "Error", "verdict": "error", "explanation": str(e)}]

def match_claims_to_timestamps(claims, transcript_data):
    """Match fact-checked claims back to transcript timestamps."""
    results = []
    
    for claim in claims:
        # Try to find the claim text in the transcript
        claim_text = claim.get('claim', '').lower()
        context_text = claim.get('context', '').lower()
        
        best_match_time = 0
        best_match_score = 0
        
        # Search for matches in transcript
        for entry in transcript_data:
            entry_text = entry['text'].lower()
            
            # Simple matching - look for claim keywords in transcript
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

def main():
    video_id = os.environ.get('VIDEO_ID')
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not video_id or not api_key:
        print("Missing required environment variables")
        return
    
    print(f"Processing video: {video_id}")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Get transcript
    transcript = get_transcript(video_id)
    if not transcript:
        print("Failed to get transcript")
        return
    
    # Format transcript
    full_text, transcript_data = format_transcript(transcript)
    print(f"Transcript length: {len(full_text)} characters")
    
    # Fact check
    claims = fact_check_content(full_text, client)
    print(f"Found {len(claims)} claims to check")
    
    # Match to timestamps
    results = match_claims_to_timestamps(claims, transcript_data)
    
    # Save results
    output_path = f"results/{video_id}.json"
    os.makedirs("results", exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'video_id': video_id,
            'processed_at': None,  # GitHub Actions will add timestamp via commit
            'claims': results
        }, f, indent=2)
    
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
