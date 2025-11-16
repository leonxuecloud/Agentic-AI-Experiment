# Customer Issue Documentation Template

## Incident Information
- **Ticket ID:** {{ticketId}}
- **Customer Name:** {{customerName}}
- **Issue Type:** {{issueType}}
- **Priority:** {{priority}}
- **Date Reported:** {{dateReported}}
- **Support Engineer:** {{supportEngineer}}

---

## Issue Description

### Customer-Reported Problem
*Describe the issue in the customer's own words*

### Symptoms and Impact

**Customer Impact:**
- [ ] Cannot access account/service
- [ ] Feature not working as expected
- [ ] Performance degradation (slow response)
- [ ] Data synchronization problems
- [ ] Error messages appearing
- [ ] Service unavailable/outage
- [ ] Other: ___________

**Business Impact:**
- **Severity:** [Critical / High / Medium / Low]
- **Users Affected:** [Number or percentage]
- **Work Blocked:** [Yes / No - describe]
- **Revenue Impact:** [If applicable]

### Reproduction Steps

**How to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. **Expected Result:** [What should happen]
5. **Actual Result:** [What actually happens]

**Reproducibility:** [Always / Intermittent (XX%) / One-time]

---

## Environment Details

### System Configuration
- **Product/Service:** [Product name and module]
- **Version:** [Version number or build]
- **Platform:** [OS, browser, device]
- **Browser:** [Name and version]
- **Account Type:** [Free / Professional / Enterprise]
- **Region:** [Geographic region or data center]
- **Last Known Working:** [Date/time if known]

### User Context
- **User Role:** [Admin / User / etc.]
- **Permissions:** [Relevant access levels]
- **Customizations:** [Any custom settings]
- **Integrations:** [Connected services]

---

## Troubleshooting Investigation

### Initial Assessment

**Timestamp:** [When investigation started]
**Initial Hypothesis:** [What you suspect the cause might be]

### Troubleshooting Steps Performed

#### Step 1: [Action Taken]
**What was checked:** [Specific check performed]

**Method:** [How you checked]

**Result:** [What you found]

**Conclusion:** [What this tells us]

---

#### Step 2: [Action Taken]
**What was checked:** [Specific check performed]

**Method:** [How you checked]

**Result:** [What you found]

**Conclusion:** [What this tells us]

---

#### Step 3: [Action Taken]
**What was checked:** [Specific check performed]

**Method:** [How you checked]

**Result:** [What you found]

**Conclusion:** [What this tells us]

---

### Diagnostic Data Collected

#### Error Messages
```
[Paste exact error messages here]
[Include error codes if available]
```

#### Log Entries
```
[Relevant log entries with timestamps]
[Filter to most relevant information]
```

#### Screenshots/Evidence
- **Screenshot 1:** [Description and link]
- **Screenshot 2:** [Description and link]
- **Video Recording:** [Link if available]

#### Network/API Analysis
- **Failed API Calls:** [List with status codes]
- **Slow Endpoints:** [Response times]
- **Network Errors:** [Connection issues]

---

## Root Cause Analysis

### What We Found

**Root Cause Category:**
- [ ] User Error (training or misunderstanding)
- [ ] Known Issue (documented with workaround)
- [ ] Software Bug (requires engineering fix)
- [ ] Configuration Problem (settings incorrect)
- [ ] Infrastructure Issue (server/network/database)
- [ ] Third-party Service (external dependency)
- [ ] Data Integrity (corruption or inconsistency)
- [ ] Performance/Capacity (resource constraints)

### Technical Explanation
*[Detailed technical explanation of the root cause]*

**Why It Occurred:**
[Explain the sequence of events or conditions that led to the issue]

**Contributing Factors:**
- [Factor 1]
- [Factor 2]
- [Factor 3]

### Similar Incidents
- **Related Tickets:** [List ticket IDs]
- **Pattern Analysis:** [Is this part of a larger trend?]
- **Frequency:** [How often does this occur?]

---

## Resolution

### Solution Implemented

**Status:**
- [ ] Resolved (permanent fix)
- [ ] Workaround Provided (temporary solution)
- [ ] Escalated to Engineering (requires code fix)
- [ ] Waiting for Customer Response
- [ ] External Dependency (waiting on third-party)

### Actions Taken

#### Step 1: [Action]
**What was done:** [Detailed description]

**Why:** [Rationale for this action]

**Result:** [Outcome]

---

#### Step 2: [Action]
**What was done:** [Detailed description]

**Why:** [Rationale for this action]

**Result:** [Outcome]

---

#### Step 3: [Action]
**What was done:** [Detailed description]

**Why:** [Rationale for this action]

**Result:** [Outcome]

---

### Verification Process

**Testing Performed:**
- [ ] Reproduced original issue
- [ ] Applied fix/workaround
- [ ] Verified issue is resolved
- [ ] Tested edge cases
- [ ] Checked for side effects
- [ ] Customer confirmed resolution

**Verification Details:**
[Describe how you verified the fix works]

**Test Results:**
[Document test outcomes]

---

## Customer Communication Log

### Initial Response

**Sent:** [Timestamp]
**Response Time:** [Minutes from ticket creation]

**Message:**
```
[Copy of initial response sent to customer]
```

---

### Progress Updates

**Update 1 - Sent:** [Timestamp]
```
[Copy of update message]
```

**Update 2 - Sent:** [Timestamp]
```
[Copy of update message]
```

---

### Resolution Communication

**Sent:** [Timestamp]
**Total Resolution Time:** [Hours/days]

**Message:**
```
[Copy of resolution message sent to customer]
```

**Customer Response:**
```
[Customer's confirmation or feedback]
```

---

## Follow-up Actions

### Immediate Actions (Completed)
- [x] Customer notified of resolution
- [x] Solution verified and tested
- [x] Documentation updated
- [x] Ticket status updated

### Short-term Actions (Next 1-7 days)
- [ ] Monitor for recurrence
- [ ] Create/update knowledge base article
- [ ] Update troubleshooting documentation
- [ ] Share findings with team
- [ ] Request customer feedback/satisfaction rating

### Long-term Actions (Next 1-4 weeks)
- [ ] Report bug to engineering (if applicable)
- [ ] Update product documentation
- [ ] Improve monitoring/alerting
- [ ] Update training materials
- [ ] Review similar incidents for patterns
- [ ] Propose product improvements

---

## Knowledge Management

### Knowledge Base
- **Related KB Articles:** [Links to existing articles]
- **New KB Article Needed:** [Yes / No]
- **KB Article Title:** [Proposed title if creating new]
- **KB Category:** [Where it should be filed]

### Documentation Updates
- **Product Docs:** [Links to docs that need updating]
- **Internal Runbooks:** [Links to internal guides]
- **Training Materials:** [Links to training content]

### Team Learning
**Lessons Learned:**
- [Key takeaway 1]
- [Key takeaway 2]
- [Key takeaway 3]

**Process Improvements:**
- [Suggested improvement 1]
- [Suggested improvement 2]

---

## Metrics and Analytics

### Performance Metrics
- **First Response Time:** [X minutes]
- **Time to Resolution:** [X hours/days]
- **Number of Updates Sent:** [Count]
- **Escalations Required:** [Yes / No / Count]
- **SLA Status:** [Met / Breached]

### Customer Satisfaction
- **CSAT Score:** [If available]
- **Customer Feedback:** [Direct quotes or summary]
- **NPS Rating:** [If collected]

### Technical Metrics
- **Troubleshooting Duration:** [Time spent]
- **Tools Used:** [List of diagnostic tools]
- **Team Members Involved:** [Names and roles]
- **Knowledge Gaps Identified:** [Areas needing more training/docs]

---

## Additional Context

### Related Information
- **Product Version History:** [Recent changes or updates]
- **Known Issues List:** [Link to current known issues]
- **Change Log:** [Recent system changes]
- **Maintenance Windows:** [Recent maintenance activities]

### Future Prevention
**To Prevent Similar Issues:**
1. [Prevention measure 1]
2. [Prevention measure 2]
3. [Prevention measure 3]

**Monitoring Improvements:**
- [Suggested alert or monitoring]

**Customer Education:**
- [Topics for customer training]

---

**Incident Closed:** [Yes / No]
**Closed Date:** [Timestamp]
**Final Status:** [Resolved / Workaround / Escalated / Cannot Reproduce]
**Customer Confirmed:** [Yes / No / No Response]
