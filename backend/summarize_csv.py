import pandas as pd
import argparse
from config import OPENAI_API_KEY
import openai
import os


def merge_consecutive_speaker_lines(df):
    merged_rows = []
    prev_speaker = None
    prev_text = ""
    prev_start = None
    prev_end = None
    for idx, row in df.iterrows():
        speaker = row['speaker']
        text = str(row['text']).strip()
        start = row['timestamp_start']
        end = row['timestamp_end']
        if prev_speaker == speaker:
            # Merge with previous
            prev_text += " " + text
            prev_end = end
        else:
            if prev_speaker is not None:
                merged_rows.append({
                    'timestamp_start': prev_start,
                    'timestamp_end': prev_end,
                    'speaker': prev_speaker,
                    'text': prev_text.strip()
                })
            prev_speaker = speaker
            prev_text = text
            prev_start = start
            prev_end = end
    # Add last
    if prev_speaker is not None:
        merged_rows.append({
            'timestamp_start': prev_start,
            'timestamp_end': prev_end,
            'speaker': prev_speaker,
            'text': prev_text.strip()
        })
    return pd.DataFrame(merged_rows)


def format_for_llm(df):
    lines = []
    for _, row in df.iterrows():
        line = f"[{row['timestamp_start']}-{row['timestamp_end']}] {row['speaker']}: {row['text']}"
        lines.append(line)
    return '\n'.join(lines)


def call_openai_llm(prompt, system_message="You are an expert business analyst and technical writer."):
    """
    Send the prompt to OpenAI's LLM and return the response.
    """
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=8000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] Failed to call OpenAI LLM: {e}"


def format_content_with_agent(raw_content):
    """
    Dedicated formatting agent that takes raw content and formats it for beautiful UI display.
    ONLY handles visual formatting - does NOT modify content meaning or structure.
    """
    formatting_prompt = f"""
You are a markdown formatting specialist. Your job is to take raw content and format it with clean, simple markdown.

CRITICAL RULES:
- DO NOT change, summarize, or modify any content meaning
- DO NOT add, remove, or alter any information
- ONLY handle visual formatting and structure
- Preserve ALL original content exactly as provided
- Use simple, clean markdown syntax

Formatting Guidelines:
1. HEADERS: Use markdown headers (# ## ###)
   - Main titles: # (single hash)
   - Section headers: ## (double hash)
   - Sub-sections: ### (triple hash)

2. LISTS: Use markdown lists
   - Bullet lists: - or *
   - Nested lists: Proper indentation

3. STRUCTURED DATA: For task lists, action items, or structured information, use simple bullet points instead of complex tables:
   - Use bullet points with clear labels
   - Format as: **Label:** Value
   - Keep it simple and readable
   - Avoid complex table structures

4. TEXT FORMATTING:
   - Bold: **text** for emphasis
   - Italics: *text* for subtle emphasis
   - Keep formatting minimal and clean

5. STRUCTURE:
   - Use clear section breaks with headers
   - Add proper spacing between sections
   - Keep paragraphs readable
   - Maintain logical flow

6. SIMPLICITY:
   - Avoid complex tables with many columns
   - Use simple bullet points for structured data
   - No excessive line breaks or decorative characters
   - Clean, professional appearance
   - Easy to read and scan

The output should be clean markdown that renders beautifully in a web interface while preserving ALL original content exactly.

Format the following content (preserve ALL information):

{raw_content}
"""
    
    try:
        formatted_content = call_openai_llm(
            formatting_prompt, 
            system_message="You are a markdown formatting specialist. Your ONLY job is visual formatting with clean markdown syntax - never modify content meaning or structure. Preserve all original information exactly."
        )
        return formatted_content
    except Exception as e:
        print(f"[WARNING] Formatting agent failed: {e}")
        # Fallback: basic markdown cleanup (preserves content)
        return basic_markdown_cleanup(raw_content)


def basic_markdown_cleanup(content):
    """
    Fallback function to clean up basic markdown if formatting agent fails.
    Preserves markdown syntax for UI rendering.
    """
    import re
    
    # Clean up excessive whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Ensure proper spacing around headers
    content = re.sub(r'^#{1,6}\s+', lambda m: f'\n{m.group(0)}', content, flags=re.MULTILINE)
    
    # Clean up list formatting
    content = re.sub(r'^\s*[-*]\s+', '- ', content, flags=re.MULTILINE)
    
    # Ensure proper table formatting
    content = re.sub(r'\|-+\|', '| --- |', content)
    
    return content.strip()


def main():
    parser = argparse.ArgumentParser(description="Prepare dialog CSV for LLM business requirements extraction.")
    parser.add_argument("csv_file", type=str, help="Path to dialog CSV file")
    parser.add_argument("--output", type=str, default=None, help="Output file for LLM response (should be in document/ subfolder)")
    parser.add_argument("--prompt", type=str, default=None, help="Custom prompt for LLM (overrides default)")
    parser.add_argument("--instructions", type=str, default=None, help="Additional instructions for the agent")
    parser.add_argument("--no-formatting", action="store_true", help="Skip formatting agent (output raw content)")
    args = parser.parse_args()

    if args.output:
        parent_dir = os.path.dirname(args.output)
        if not os.path.exists(parent_dir):
            raise FileNotFoundError(f"Summary output directory does not exist: {parent_dir}")

    df = pd.read_csv(args.csv_file)
    merged_df = merge_consecutive_speaker_lines(df)
    llm_input = format_for_llm(merged_df)

    if args.prompt:
        if args.prompt == 'ENV_VAR':
            # Get prompt from environment variable
            prompt = os.environ.get('CUSTOM_PROMPT', '')
            if not prompt:
                print("[WARNING] CUSTOM_PROMPT environment variable not found, using default prompt")
                prompt = None
        else:
            prompt = args.prompt
    
    if not prompt:
        prompt = f"""
You are an expert business analyst and technical writer.

Based on the meeting transcript I will provide, identify and extract all distinct business requirements discussed by the stakeholders.
Pls note that the transcript is between a vendor (us) and a client (them).
There could be multiple requirements discussed in the transcript.
Pls clearly identify the requirements and break them down into separate sections.
Retain the technical details from the conversation.

For each requirement:
- Give it a clear, descriptive title if the speakers do not explicityly provide one
- Provide a detailed description and rationale
- Break down the functional steps involved, with sub-steps and explanations
- List any dependencies or external systems involved
- Capture technical constraints or assumptions

If more than one requirement is discussed, clearly split them into separate sections.

The goal is to make the document clear enough and detailed enough that a development team can directly begin working on implementation.

Format your response with clear sections for:
Requirement Title
Summary
Functional Steps
Output Deliverables
Dependencies
Additional Notes - That capture additional technical details
Next Action Items

Focus on content quality and structure. The formatting will be handled separately.
"""
    if args.instructions:
        if args.instructions == 'ENV_VAR':
            # Get instructions from environment variable
            instructions = os.environ.get('CUSTOM_INSTRUCTIONS', '')
            if not instructions:
                print("[WARNING] CUSTOM_INSTRUCTIONS environment variable not found")
                instructions = None
        else:
            instructions = args.instructions
        
        if instructions:
            prompt = f"{prompt}\n\nAdditional instructions from user: {instructions}. Make sure you adhere to the user instructions/information if given"
    
    prompt = f"{prompt}\n\nHere is the transcript:\n{llm_input}"

    # Print the final prompt for debugging
    print("=== FINAL PROMPT SENT TO MAIN AGENT ===")
    print(f"Prompt source: {'Environment variable' if args.prompt == 'ENV_VAR' else 'Command line argument' if args.prompt else 'Default'}")
    print(f"Instructions source: {'Environment variable' if args.instructions == 'ENV_VAR' else 'Command line argument' if args.instructions else 'None'}")
    print(f"Prompt length: {len(prompt)}")
    print(f"Prompt preview: {prompt[:300]}...")
    print("=== END PROMPT PREVIEW ===")

    # Step 1: Call the main content generation agent
    print("\n=== STEP 1: GENERATING CONTENT ===")
    raw_content = call_openai_llm(prompt)
    print(f"Raw content generated ({len(raw_content)} characters)")

    # Step 2: Format the content with the formatting agent (unless disabled)
    if not args.no_formatting:
        print("\n=== STEP 2: FORMATTING CONTENT ===")
        formatted_content = format_content_with_agent(raw_content)
        print(f"Content formatted ({len(formatted_content)} characters)")
        final_content = formatted_content
    else:
        print("\n=== SKIPPING FORMATTING (--no-formatting flag used) ===")
        final_content = raw_content

    # Output the final content
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"\nFinal content written to {args.output}")
    else:
        print("\n=== FINAL FORMATTED OUTPUT ===")
        print(final_content)

if __name__ == "__main__":
    main() 