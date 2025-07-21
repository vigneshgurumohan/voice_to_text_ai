# Custom Templates Directory

This directory contains user-created custom prompt templates that are saved through the frontend interface.

## How it works

1. **Frontend Creation**: Users can edit prompts and save them as custom templates
2. **Server Storage**: Custom templates are saved as `.txt` files in this directory
3. **Naming Convention**: Files are named with the pattern `custom_templates.{user_provided_name}.txt`
4. **Automatic Loading**: The backend automatically loads these templates along with other prompts

## File Structure

```
custom_templates/
├── README.md                    # This file
├── custom_templates.my_prompt.txt    # User-created template
├── custom_templates.technical_analysis.txt
└── custom_templates.project_plan.txt
```

## Management

- **Create**: Via frontend "Save as Custom Prompt" feature
- **Edit**: Via frontend prompt editing modal
- **Delete**: Via frontend delete button (🗑️)
- **Rename**: Via frontend rename button (✏️)

## Backup

These files are part of your project and can be:
- Version controlled with Git
- Backed up with your project
- Shared with team members
- Migrated to other environments

## Notes

- Custom templates are automatically loaded by the prompt manager
- They appear in the frontend dropdown under "Custom Templates"
- Users can manage them directly through the frontend interface
- The backend API handles all CRUD operations for these templates 