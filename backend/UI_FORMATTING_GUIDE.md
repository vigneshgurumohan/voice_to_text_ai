# UI Formatting Guide for Document Display

## Overview
This guide defines how the formatting agent should structure content for optimal display in the web UI. The formatting agent ONLY handles visual presentation - it never modifies content meaning or structure.

## Content Structure Standards

### 1. Headers & Titles

#### Main Document Title
```
BUSINESS REQUIREMENTS DOCUMENT
Meeting: [Meeting Name/Date]
Generated: [Timestamp]
```

#### Section Headers
```
REQUIREMENT 1: [Requirement Name]
REQUIREMENT 2: [Requirement Name]
```

#### Sub-section Headers
```
Summary
Functional Steps
Output Deliverables
Dependencies
Additional Notes
Next Action Items
```

### 2. Lists & Bullet Points

#### Priority Lists
```
HIGH PRIORITY (This Week):
• Task 1: [Description] - Assignee: [Name] - Deadline: [Date]
• Task 2: [Description] - Assignee: [Name] - Deadline: [Date]

MEDIUM PRIORITY (Next 2 Weeks):
• Task 3: [Description] - Assignee: [Name] - Deadline: [Date]
```

#### Action Items
```
Action Items:
1. [Task Description]
   Assignee: [Name]
   Deadline: [Date]
   Dependencies: [List]
   Notes: [Additional information]

2. [Task Description]
   Assignee: [Name]
   Deadline: [Date]
   Dependencies: [List]
   Notes: [Additional information]
```

#### Functional Steps
```
Functional Steps:
Step 1: [Step Description]
   • Sub-step 1.1: [Description]
   • Sub-step 1.2: [Description]

Step 2: [Step Description]
   • Sub-step 2.1: [Description]
   • Sub-step 2.2: [Description]
```

### 3. Tables (Converted to Clean Text)

#### Before (Markdown):
```
| Task | Assignee | Deadline | Dependencies | Notes |
|------|----------|----------|--------------|-------|
| Segregate data | Fauja | End of week | Access to data | WPG and Private Banking |
```

#### After (Clean Text):
```
TASK ASSIGNMENTS:

Task: Segregate customer data by business type
Assignee: Fauja
Deadline: End of week
Dependencies: Access to customer data
Notes: Segregate WPG and Private Banking; Private sector is out of scope

Task: Remove accounts with customer liability
Assignee: Fauja
Deadline: End of week
Dependencies: Completion of data segregation
Notes: Only classic and WPG segments are in scope
```

### 4. Content Sections

#### Complete Requirement Structure
```
REQUIREMENT 1: Customer Data Segregation

Summary:
[Clear, concise summary of the requirement]

Functional Steps:
1. [Step description]
   • [Sub-step details]
   • [Sub-step details]

2. [Step description]
   • [Sub-step details]

Output Deliverables:
• [Deliverable 1]
• [Deliverable 2]

Dependencies:
• [Dependency 1]
• [Dependency 2]

Additional Notes:
[Technical details, constraints, assumptions]

Next Action Items:
1. [Action item] - Assignee: [Name] - Deadline: [Date]
2. [Action item] - Assignee: [Name] - Deadline: [Date]
```

### 5. Visual Hierarchy

#### Spacing Standards
- **Main sections**: 2 line breaks between major sections
- **Sub-sections**: 1 line break between sub-sections
- **List items**: Consistent indentation
- **Table conversions**: Clear spacing between rows

#### Typography Guidelines
- **Main titles**: ALL CAPS for emphasis
- **Section headers**: Title Case with clear separation
- **Sub-headers**: Sentence case with consistent formatting
- **Body text**: Normal case, clear and readable

### 6. Special Content Types

#### Technical Constraints
```
Technical Constraints:
• [Constraint 1]: [Explanation]
• [Constraint 2]: [Explanation]
```

#### Assumptions
```
Assumptions:
• [Assumption 1]: [Context]
• [Assumption 2]: [Context]
```

#### Risks
```
Risks:
• [Risk 1]: [Impact and mitigation]
• [Risk 2]: [Impact and mitigation]
```

## Formatting Agent Rules

### DO:
- ✅ Preserve ALL original content exactly
- ✅ Convert markdown tables to clean, readable text
- ✅ Use consistent bullet points (•)
- ✅ Apply clear visual hierarchy
- ✅ Add proper spacing for readability
- ✅ Make content mobile-friendly
- ✅ Use professional formatting standards

### DON'T:
- ❌ Modify any content meaning
- ❌ Add or remove information
- ❌ Summarize or condense content
- ❌ Change technical details
- ❌ Alter requirements or specifications
- ❌ Use markdown syntax in output

## Example Output

### Input (Raw from Main Agent):
```
**Action Items and Tasks Extracted from Meeting Transcript**

| Task | Assignee | Deadline | Dependencies | Notes |
|------|----------|----------|--------------|-------|
| Segregate data | Fauja | End of week | Access to data | WPG and Private Banking |
```

### Output (Formatted for UI):
```
ACTION ITEMS AND TASKS EXTRACTED FROM MEETING TRANSCRIPT

TASK ASSIGNMENTS:

Task: Segregate customer data by business type
Assignee: Fauja
Deadline: End of week
Dependencies: Access to customer data
Notes: Segregate WPG and Private Banking; Private sector is out of scope
```

This structure ensures:
- Professional appearance
- Easy scanning and reading
- Mobile compatibility
- Consistent formatting
- Content preservation
- Beautiful UI display 