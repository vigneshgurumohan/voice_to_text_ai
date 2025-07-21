# Prompts Repository

This directory contains all the prompts used by the Voice-to-Text AI application for generating different types of summaries and documents.

## Structure

```
prompts/
├── README.md              # This file
├── general_summary.txt    # General meeting summary prompt
├── fsd_summary.txt        # Functional Specification Document prompt
├── technical_summary.txt  # Technical requirements summary
├── action_items.txt       # Action items extraction prompt
├── meeting_minutes.txt    # Meeting minutes format prompt
└── custom_templates/      # Directory for custom prompt templates
    ├── project_plan.txt
    ├── bug_report.txt
    └── user_story.txt
```

## Usage

### Adding New Prompts
1. Create a new `.txt` file in the appropriate directory
2. Use descriptive filename (e.g., `technical_summary.txt`)
3. Write your prompt in plain text
4. The backend will automatically detect and load the new prompt

### Editing Prompts
1. Simply edit the `.txt` file directly
2. Changes take effect immediately (no restart required)
3. Use clear, descriptive language
4. Include placeholders for dynamic content if needed

### Deleting Prompts
1. Remove the `.txt` file from the prompts directory
2. The backend will no longer offer this prompt type
3. Update any frontend references if needed

## Prompt Guidelines

### Best Practices
- **Clear Instructions**: Be specific about what you want the AI to extract
- **Context**: Provide enough context for the AI to understand the task
- **Format**: Specify the desired output format
- **Length**: Keep prompts concise but comprehensive
- **Placeholders**: Use `{transcript}` for the transcript content

### Example Structure
```
You are an expert [role]. 

Based on the meeting transcript I will provide, [specific task].

Requirements:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Output Format:
[describe the desired output format]

Transcript:
{transcript}
```

## Available Prompts

### Core Prompts
- **general_summary.txt**: General meeting highlights and key points
- **fsd_summary.txt**: Functional Specification Document generation
- **technical_summary.txt**: Technical requirements and specifications
- **action_items.txt**: Action items and task extraction
- **meeting_minutes.txt**: Formal meeting minutes format

### Custom Templates
- **project_plan.txt**: Project planning and roadmap
- **bug_report.txt**: Bug and issue documentation
- **user_story.txt**: User story and requirement extraction

## Backend Integration

The backend automatically:
- Scans the prompts directory for new files
- Loads prompts dynamically
- Provides API endpoints to list available prompts
- Allows runtime prompt selection and customization 