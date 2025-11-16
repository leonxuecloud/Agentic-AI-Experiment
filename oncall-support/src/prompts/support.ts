/**
 * Support Team Prompts
 * 
 * Optimized MCP prompt system for customer support workflows.
 * 
 * This module provides structured templates for:
 * - Customer issue documentation and tracking
 * - Systematic troubleshooting guides
 * - Professional customer communication
 * - Engineering escalation procedures
 * - Knowledge base article creation
 * 
 * All prompts follow best practices from the triage system including:
 * - Structured workflows and checklists
 * - Clear step-by-step processes
 * - Comprehensive documentation requirements
 * - Metrics and quality tracking
 * 
 * Related Resources:
 * - System Prompt: ../templates/oncall-support-system-prompt.md
 * - Issue Template: ../templates/customer-issue-template.md
 * - Troubleshooting Template: ../templates/troubleshooting-guide-template.md
 */

import { readFileSync } from 'fs';
import { join } from 'path';

/**
 * Helper: Load markdown template from templates directory
 */
function loadTemplate(filename: string): string {
  try {
    const templatePath = join(__dirname, '..', 'templates', filename);
    return readFileSync(templatePath, 'utf-8');
  } catch (error) {
    console.error(`Failed to load template ${filename}:`, error);
    return '';
  }
}

/**
 * Helper: Replace template variables
 */
function fillTemplate(template: string, params: Record<string, any>): string {
  let filled = template;
  for (const [key, value] of Object.entries(params)) {
    const placeholder = new RegExp(`{{${key}}}`, 'g');
    filled = filled.replace(placeholder, value !== undefined ? String(value) : '');
  }
  return filled;
}

/**
 * Cache for loaded templates
 */
const templateCache: Record<string, string> = {};

/**
 * Helper: Get cached template or load it
 */
function getTemplate(filename: string): string {
  if (!templateCache[filename]) {
    templateCache[filename] = loadTemplate(filename);
  }
  return templateCache[filename];
}

/**
 * Prompt: Customer Issue Documentation
 * Helps support engineers document customer issues thoroughly using optimized template
 */
export function customerIssuePrompt(params: {
  ticketId: string;
  customerName: string;
  issueType: string;
  priority?: string;
}): string {
  const template = getTemplate('customer-issue-template.md');
  
  return fillTemplate(template, {
    ticketId: params.ticketId,
    customerName: params.customerName,
    issueType: params.issueType,
    priority: params.priority || 'Medium',
    dateReported: new Date().toISOString().split('T')[0],
    supportEngineer: '[Your Name]'
  });
}

/**
 * Prompt: Troubleshooting Guide Generator
 * Creates comprehensive step-by-step troubleshooting guides for common issues
 */
export function troubleshootingGuidePrompt(params: {
  issueName: string;
  product: string;
  difficulty?: string;
}): string {
  const template = getTemplate('troubleshooting-guide-template.md');
  
  return fillTemplate(template, {
    issueName: params.issueName,
    product: params.product,
    difficulty: params.difficulty || 'Intermediate',
    estimatedTime: '30-60',
    lastUpdated: new Date().toISOString().split('T')[0],
    author: '[Your Name]'
  });
}

/**
 * Prompt: Customer Communication Template
 * Professional templates for customer responses
 */
export function customerCommunicationPrompt(params: {
  type: 'initial_response' | 'update' | 'resolution' | 'escalation' | 'apology';
  ticketId: string;
  customerName: string;
  issueType?: string;
}): string {
  const templates = {
    initial_response: `Subject: Re: ${params.issueType || 'Your Support Request'} [Ticket #${params.ticketId}]

Hi ${params.customerName},

Thank you for contacting support. I've received your ticket regarding [brief issue description] and I'm here to help.

**What I understand so far:**
- [Summarize the issue]
- [Impact on customer]
- [What they're trying to accomplish]

**Next Steps:**
1. [What you're going to investigate]
2. [Any information you need from them]
3. [Expected timeline for response]

I'll start looking into this right away and will update you within [timeframe]. If you have any additional information that might help (screenshots, error messages, etc.), please feel free to send them over.

Best regards,
[Your Name]
[Your Title]`,

    update: `Subject: Update on Your Issue [Ticket #${params.ticketId}]

Hi ${params.customerName},

I wanted to give you an update on your ticket.

**What we've done so far:**
- [Investigation step 1]
- [Investigation step 2]
- [Findings]

**Current Status:**
[Brief status update - still investigating / found the cause / testing a fix]

**Next Steps:**
1. [What's happening next]
2. [Expected timeline]
3. [What you need from customer, if anything]

I'll continue working on this and will have another update for you by [time/date]. Please don't hesitate to reach out if you have any questions.

Best regards,
[Your Name]`,

    resolution: `Subject: ✅ Resolved: ${params.issueType || 'Your Issue'} [Ticket #${params.ticketId}]

Hi ${params.customerName},

Great news! I've resolved the issue you reported.

**What the Problem Was:**
[Explain the root cause in customer-friendly language]

**What We Did to Fix It:**
[Explain the solution]

**What You Need to Do:**
1. [Any actions required from customer]
2. [How to verify it's working]
3. [Any follow-up recommendations]

**Testing and Verification:**
I've tested the fix and confirmed that [specific outcome]. Please try it on your end and let me know if everything is working as expected.

**To Prevent This in the Future:**
[Optional: preventive measures or best practices]

Is there anything else I can help you with? If the issue is fully resolved, feel free to close this ticket, or I'll automatically close it in [X] days if I don't hear back.

Best regards,
[Your Name]

---
**Support Tip:** [Optional helpful tip related to the issue]`,

    escalation: `Subject: Your Issue Requires Additional Investigation [Ticket #${params.ticketId}]

Hi ${params.customerName},

Thank you for your patience as I've been investigating your issue.

**Current Situation:**
After thorough troubleshooting, I've determined that your issue requires deeper technical investigation from our engineering team. This is to ensure we provide you with the most accurate and effective solution.

**What This Means:**
- Your ticket has been escalated to our engineering team
- This is not uncommon for complex issues
- You'll have both my support and our engineers working on this

**What Happens Next:**
1. Engineering team will review within [timeframe]
2. They may reach out for additional information
3. I'll continue to coordinate and keep you updated
4. Expected resolution timeline: [timeframe]

**What I've Shared with Engineering:**
- Complete troubleshooting steps taken
- All diagnostic data collected
- Your specific configuration details
- Impact on your workflow

I remain your primary point of contact and will update you [daily/every X hours] on progress. If you have any questions or concerns in the meantime, please don't hesitate to reach out.

Best regards,
[Your Name]

P.S. We take these issues seriously and appreciate your patience as we work toward a resolution.`,

    apology: `Subject: Our Apologies for the Inconvenience [Ticket #${params.ticketId}]

Hi ${params.customerName},

I want to sincerely apologize for the trouble you've experienced with [issue description].

**We Understand:**
- This has impacted your ability to [describe impact]
- You've spent [time] dealing with this issue
- This isn't the experience we want you to have

**What Went Wrong:**
[Brief, honest explanation of what happened]

**How We're Making It Right:**
1. [Immediate fix/resolution]
2. [Compensation if applicable]
3. [Steps to prevent recurrence]

**What We're Doing to Prevent This:**
- [Improvement 1]
- [Improvement 2]
- [Process change]

Your feedback helps us improve, and we genuinely appreciate your patience. If there's anything more I can do to help resolve this situation, please let me know.

Best regards,
[Your Name]
[Your Title]

---
If you have any concerns about how this was handled, please feel free to reach out to my manager at [escalation contact].`
  };

  return templates[params.type] || templates.initial_response;
}

/**
 * Prompt: Escalation Template
 * For escalating issues to engineering or management
 */
export function escalationPrompt(params: {
  ticketId: string;
  customerName: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  issueType: string;
}): string {
  return `# Escalation Request: ${params.ticketId}

## Escalation Summary
- **Ticket ID:** ${params.ticketId}
- **Customer:** ${params.customerName}
- **Severity:** ${params.severity.toUpperCase()}
- **Issue Type:** ${params.issueType}
- **Escalated By:** [Your Name]
- **Escalation Date:** ${new Date().toISOString()}

## Why This Needs Escalation

**Issue Category:**
- [ ] Bug requiring engineering fix
- [ ] Feature limitation
- [ ] Performance issue
- [ ] Data integrity concern
- [ ] Security issue
- [ ] Multiple customers affected
- [ ] VIP/Enterprise customer
- [ ] Business critical functionality

**Impact Assessment:**
- **Customer Impact:** [High/Medium/Low]
- **Number of Users Affected:** [number]
- **Business Impact:** [Revenue/reputation/compliance]
- **Workaround Available:** [Yes/No - describe if yes]

## Detailed Issue Description

### What's Happening
*[Clear description of the issue from technical perspective]*

### Expected Behavior
*[What should happen]*

### Actual Behavior
*[What is actually happening]*

### Frequency
- [ ] Happens every time
- [ ] Intermittent (XX% of the time)
- [ ] Happened once
- [ ] Getting worse over time

## Troubleshooting Already Completed

### Steps Taken
1. **[Action 1]**
   - Result: [Outcome]
   - Conclusion: [What this ruled out]

2. **[Action 2]**
   - Result: [Outcome]
   - Conclusion: [What this ruled out]

3. **[Action 3]**
   - Result: [Outcome]
   - Conclusion: [What this ruled out]

### What We've Ruled Out
- ✓ [Cause 1 - ruled out because...]
- ✓ [Cause 2 - ruled out because...]
- ✓ [Cause 3 - ruled out because...]

### What We Suspect
- ⚠️ [Possible cause 1 - evidence]
- ⚠️ [Possible cause 2 - evidence]

## Technical Details

### Environment
- **Product Version:** [version]
- **Platform:** [OS/browser]
- **Account Type:** [Free/Paid/Enterprise]
- **Configuration:** [Relevant settings]

### Error Messages/Logs
\`\`\`
[Paste relevant error messages]
\`\`\`

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. **Result:** [What happens]

**Reproducibility:** [Always/Sometimes/Rare]

### Evidence
- **Screenshots:** [Attached/linked]
- **Log Files:** [Attached/linked]
- **Video:** [If available]
- **Network Traces:** [If applicable]

## Customer Context

### Customer Information
- **Account Tier:** [Free/Professional/Enterprise]
- **Contract Value:** [If applicable]
- **Account Age:** [How long they've been customer]
- **Previous Issues:** [Number of prior tickets]

### Customer Communication
- **Last Update Sent:** [Date/time]
- **Customer Expectation:** [What they're expecting]
- **Customer Patience Level:** [Patient/Concerned/Frustrated/Angry]
- **Promised Timeline:** [What you told them]

### Business Impact for Customer
*[How this affects their business/work]*

## Requested Action

### What We Need
- [ ] Engineering investigation
- [ ] Code fix required
- [ ] Configuration change
- [ ] Database intervention
- [ ] Infrastructure adjustment
- [ ] Product decision needed

### Priority Recommendation
**Suggested Priority:** [P0/P1/P2/P3]

**Justification:**
- [Reason 1]
- [Reason 2]
- [Reason 3]

### Timeline Needed
- **Customer Expects Response:** [Date/time]
- **Critical Deadline:** [If any]
- **Recommended Target:** [Your suggestion]

## Proposed Solutions

### Option 1: [Solution Name]
**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Effort:** [High/Medium/Low]

### Option 2: [Alternative Solution]
**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Effort:** [High/Medium/Low]

### Temporary Workaround
**While permanent fix is developed:**
[Describe workaround if available]

## Additional Context

### Similar Issues
- **Related Tickets:** [Ticket IDs]
- **Pattern:** [If this is recurring]
- **Trend:** [Getting more frequent?]

### Supporting Information
- **KB Articles:** [Relevant articles]
- **Documentation:** [Related docs]
- **Forum Posts:** [Community discussions]

---

## Escalation Checklist
- [ ] Tried all standard troubleshooting steps
- [ ] Gathered complete technical details
- [ ] Documented customer impact
- [ ] Checked for similar existing issues
- [ ] Prepared workaround (if available)
- [ ] Set customer expectations
- [ ] Attached all relevant evidence
- [ ] Reviewed with team lead (if required)

**Note to Engineering:** [Any additional context or requests]
`;
}

/**
 * Prompt: Knowledge Base Article Creator
 * Creates comprehensive KB articles from support experiences
 */
export function knowledgeBasePrompt(params: {
  articleTitle: string;
  category: string;
  difficulty?: string;
}): string {
  return `# KB Article: ${params.articleTitle}

## Article Metadata
- **Title:** ${params.articleTitle}
- **Category:** ${params.category}
- **Difficulty:** ${params.difficulty || 'Beginner'}
- **Last Updated:** ${new Date().toISOString().split('T')[0]}
- **Article ID:** [Auto-generated]
- **Author:** [Your Name]

---

## Article Summary
*[2-3 sentence overview of what this article covers and who it's for]*

**Keywords:** [keyword1, keyword2, keyword3, keyword4]

---

## Who This Article Is For
- [ ] End users (customers)
- [ ] Administrators
- [ ] Developers
- [ ] Support team only

**Prerequisite Knowledge:**
- [Concept/skill 1 reader should know]
- [Concept/skill 2 reader should know]

---

## Problem Description

### What Users Experience
*[Describe the issue or question in user-friendly terms]*

**Common Symptoms:**
- [Symptom 1]
- [Symptom 2]
- [Symptom 3]

**When This Happens:**
- [Common scenario 1]
- [Common scenario 2]

---

## Quick Answer

> **TL;DR:** [One-paragraph quick solution for those who just need the answer]

---

## Detailed Solution

### Step-by-Step Instructions

#### Step 1: [Action Name]
**What to do:**
[Clear, detailed instructions]

**Example:**
\`\`\`
[Code, command, or screenshot example]
\`\`\`

**Expected Result:**
[What should happen after this step]

---

#### Step 2: [Next Action]
**What to do:**
[Clear, detailed instructions]

**Tips:**
- 💡 [Helpful tip]
- ⚠️ [Warning or caution]

**Example:**
\`\`\`
[Code, command, or screenshot example]
\`\`\`

---

#### Step 3: [Final Action]
**What to do:**
[Clear, detailed instructions]

**Verification:**
[How to confirm it worked]

---

## Alternative Methods

### Method 2: [Alternative Approach]
**When to use this:** [Scenario where this is better]

**Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Pros/Cons:**
- ✅ [Advantage]
- ❌ [Disadvantage]

---

## Troubleshooting

### Issue: [Common Problem #1]
**Symptoms:** [How to recognize this]

**Solution:**
[How to fix it]

---

### Issue: [Common Problem #2]
**Symptoms:** [How to recognize this]

**Solution:**
[How to fix it]

---

## Best Practices

### Do's ✅
- ✅ [Best practice 1]
- ✅ [Best practice 2]
- ✅ [Best practice 3]

### Don'ts ❌
- ❌ [Common mistake 1]
- ❌ [Common mistake 2]
- ❌ [Common mistake 3]

---

## Examples

### Example 1: [Use Case Name]
**Scenario:** [Describe the situation]

**Solution:**
\`\`\`
[Step-by-step with examples]
\`\`\`

**Result:** [What the outcome looks like]

---

### Example 2: [Another Use Case]
**Scenario:** [Describe the situation]

**Solution:**
\`\`\`
[Step-by-step with examples]
\`\`\`

**Result:** [What the outcome looks like]

---

## FAQ

**Q: [Common question 1]?**
A: [Clear answer]

**Q: [Common question 2]?**
A: [Clear answer]

**Q: [Common question 3]?**
A: [Clear answer]

---

## Additional Resources

### Related Articles
- [KB Article Title 1] - [Brief description]
- [KB Article Title 2] - [Brief description]

### Video Tutorials
- [Video Title] - [Link] - [Duration]

### Documentation
- [Doc Section] - [Link]

### Community
- [Forum Discussion] - [Link]

---

## Technical Details
*[Optional section for advanced users or support team]*

### How It Works
[Technical explanation of the underlying mechanism]

### Limitations
- [Limitation 1]
- [Limitation 2]

### Platform Compatibility
- ✅ Windows: [Version details]
- ✅ macOS: [Version details]
- ✅ Linux: [Version details]
- ✅ Web: [Browser requirements]
- ✅ Mobile: [iOS/Android details]

---

## Feedback

**Was this article helpful?**
[Feedback mechanism]

**How can we improve this article?**
[Feedback form/comments]

---

## Version History
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| ${new Date().toISOString().split('T')[0]} | 1.0 | Initial creation | [Name] |

---

**Article Status:** ✅ Published | 📝 Draft | 🔄 Under Review
`;
}

/**
 * Prompt: Ticket Triage Assistant
 * Provides comprehensive triage analysis for support tickets (inspired by jira-triager)
 */
export function ticketTriagePrompt(params: {
  ticketId: string;
  ticketData: string;
  systemPrompt?: boolean;
}): string {
  // If systemPrompt is true, include the full system prompt guidance
  const systemGuidance = params.systemPrompt ? getTemplate('oncall-support-system-prompt.md') + '\n\n---\n\n' : '';
  
  return `${systemGuidance}# Ticket Triage Request

You have been assigned to triage the following support ticket:

**Ticket ID:** ${params.ticketId}

**Ticket Data:**
\`\`\`json
${params.ticketData}
\`\`\`

---

## Your Triage Task

Analyze this ticket and provide a comprehensive triage assessment following the structured workflow:

### 1. Understand the Issue
- Read the ticket summary, description, and any comments carefully
- Identify what the customer is experiencing
- Understand the business impact and urgency
- Check for any attachments, screenshots, or error messages

### 2. Gather Context
- Review the customer's ticket history for similar issues
- Check if this is a known issue with existing workarounds
- Search for related or duplicate tickets
- Identify any patterns or trends
- Review comments for additional clarifications already provided

### 3. Extract Critical Information
Systematically extract and verify:
- **Environment details**: Product version, platform, browser, region
- **Customer information**: Account tier, SLA requirements
- **Incident characteristics**: Symptoms, impact, frequency, reproducibility
- **Timeline**: When it started, last working state, recent changes
- **Error details**: Exact error messages, logs, stack traces

### 4. Assess Missing Information
If required information is missing or insufficient:
- Clearly identify what information is needed and why
- Prioritize questions (most critical first)
- Explain how this information will help resolve the issue
- Prepare to request specifics from the customer

### 5. Classify and Prioritize

**Incident Type:**
- Outage, Degradation, Bug, Configuration, User Error, Feature Request, or Question

**Priority Assessment:**
- **P0 - Critical**: Complete outage, data loss, security issue, all users affected
- **P1 - High**: Major functionality broken, enterprise customer, significant impact
- **P2 - Medium**: Important feature issue, workaround available, moderate impact
- **P3 - Low**: Minor issues, cosmetic problems, questions, low impact

**Consider:**
- How many users/accounts are affected?
- Is service down or degraded?
- What is the customer tier and SLA?
- Does it block critical business work?
- Are there viable workarounds?

### 6. Recommend Actions
Suggest:
- **Component/Category**: Proper categorization for routing
- **Labels**: Relevant tags for tracking (e.g., backend, api, performance, needs-investigation)
- **Team Assignment**: Which team should handle this based on technical area
- **Priority**: Recommended priority with clear justification
- **Next Steps**: Specific actions for investigation or resolution
- **Escalation**: Whether immediate engineering involvement is needed

### 7. Communicate Your Analysis
Add a well-structured comment with your triage analysis:

**Required Structure:**
\`\`\`
**Triage Summary**
[Brief overview of the issue in 1-2 sentences]

**Environment & Context**
- Product/Service: [name]
- Version: [version]
- Platform: [OS/browser]
- Customer Tier: [tier]
- Region: [region]
- Affected Users: [number or scope]

**Classification**
- Type: [Outage/Bug/Configuration/etc.]
- Priority: [P0/P1/P2/P3] - [Justification]
- Root Cause Hypothesis: [Initial assessment]

**Analysis**
[Key findings from your investigation:
- What's happening
- Why it's happening (if known)
- Impact assessment
- Evidence from logs/comments]

**Recommendations**
- Category/Component: [Suggested categorization]
- Labels: [label1, label2, label3]
- Assign To: [Team name] - [Reason]
- Priority: [Recommended priority with justification]

**Next Steps**
1. [Immediate action 1]
2. [Immediate action 2]
3. [Investigation step 3]
4. [Follow-up action 4]

**Missing Information** (if applicable)
[List specific information needed:
- What's missing
- Why it's important
- How to obtain it]

**Related Tickets** (if found)
- [TICKET-123]: Similar issue - [brief description]
- [TICKET-456]: Related pattern - [brief description]
\`\`\`

### 8. Provide Clear Next Steps
Propose actionable steps for:
- Immediate investigation actions
- Information requests from customer
- Resolution approach or workaround
- Engineering escalation if needed
- Timeline expectations

---

## Important Guidelines

**Be Thorough:**
- Check for duplicate or related tickets before making recommendations
- Review all existing comments and ticket history
- Consider technical dependencies and external factors
- Use available tools to gather diagnostic data

**Be Helpful:**
- Suggest specific, actionable next steps
- Identify missing information and explain why it's needed
- Recommend additional context or logs that would be useful
- Provide clear reasoning for all classifications and recommendations

**Be Professional:**
- Use clear, professional language
- Be empathetic to customer frustration
- Set realistic expectations
- Maintain a solution-focused approach
- Format your analysis for easy readability

**Be Efficient:**
- Focus on the most critical information first
- Don't ask questions already answered in comments
- Leverage past similar incidents for faster resolution
- Identify quick wins or workarounds when possible

---

## Success Criteria

Your triage is complete when:
- [ ] All available information has been analyzed
- [ ] Critical missing information has been identified
- [ ] Priority and classification are justified
- [ ] Clear next steps are provided
- [ ] Proper categorization and routing are recommended
- [ ] Customer communication is professional and helpful
- [ ] Time-to-resolution expectations are set

Take your time to provide a thoughtful, comprehensive triage assessment that will help the support team and customer resolve this issue effectively.
`;
}

/**
 * Export all support prompts
 */
export const supportPrompts = {
  'customer-issue': {
    name: 'customer-issue',
    description: 'Template for documenting customer issues thoroughly',
    arguments: [
      {
        name: 'ticketId',
        description: 'Jira ticket ID',
        required: true,
      },
      {
        name: 'customerName',
        description: 'Customer name',
        required: true,
      },
      {
        name: 'issueType',
        description: 'Type of issue reported',
        required: true,
      },
      {
        name: 'priority',
        description: 'Issue priority (Low/Medium/High/Critical)',
        required: false,
      },
    ],
    generator: customerIssuePrompt,
  },
  'troubleshooting-guide': {
    name: 'troubleshooting-guide',
    description: 'Generate step-by-step troubleshooting guide for common issues',
    arguments: [
      {
        name: 'issueName',
        description: 'Name of the issue to troubleshoot',
        required: true,
      },
      {
        name: 'product',
        description: 'Product name',
        required: true,
      },
      {
        name: 'difficulty',
        description: 'Difficulty level (Beginner/Intermediate/Advanced)',
        required: false,
      },
    ],
    generator: troubleshootingGuidePrompt,
  },
  'customer-communication': {
    name: 'customer-communication',
    description: 'Professional customer communication templates',
    arguments: [
      {
        name: 'type',
        description: 'Type of communication (initial_response/update/resolution/escalation/apology)',
        required: true,
      },
      {
        name: 'ticketId',
        description: 'Ticket ID',
        required: true,
      },
      {
        name: 'customerName',
        description: 'Customer name',
        required: true,
      },
      {
        name: 'issueType',
        description: 'Type of issue',
        required: false,
      },
    ],
    generator: customerCommunicationPrompt,
  },
  'escalation-template': {
    name: 'escalation-template',
    description: 'Template for escalating issues to engineering',
    arguments: [
      {
        name: 'ticketId',
        description: 'Ticket ID to escalate',
        required: true,
      },
      {
        name: 'customerName',
        description: 'Customer name',
        required: true,
      },
      {
        name: 'severity',
        description: 'Issue severity (low/medium/high/critical)',
        required: true,
      },
      {
        name: 'issueType',
        description: 'Type of issue',
        required: true,
      },
    ],
    generator: escalationPrompt,
  },
  'knowledge-base-article': {
    name: 'knowledge-base-article',
    description: 'Create comprehensive knowledge base article from support experience',
    arguments: [
      {
        name: 'articleTitle',
        description: 'Title of the KB article',
        required: true,
      },
      {
        name: 'category',
        description: 'Article category',
        required: true,
      },
      {
        name: 'difficulty',
        description: 'Difficulty level (Beginner/Intermediate/Advanced)',
        required: false,
      },
    ],
    generator: knowledgeBasePrompt,
  },
  'ticket-triage': {
    name: 'ticket-triage',
    description: 'Comprehensive ticket triage analysis with structured workflow (inspired by jira-triager)',
    arguments: [
      {
        name: 'ticketId',
        description: 'Ticket ID to triage',
        required: true,
      },
      {
        name: 'ticketData',
        description: 'Complete ticket data as JSON string',
        required: true,
      },
      {
        name: 'systemPrompt',
        description: 'Include full system prompt guidance (true/false)',
        required: false,
      },
    ],
    generator: ticketTriagePrompt,
  },
};
