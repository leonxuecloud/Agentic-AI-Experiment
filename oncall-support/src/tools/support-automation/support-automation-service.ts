/**
 * Support Automation Service - Unified support automation operations
 * Provides ticket analysis, knowledge search, and ticket triage functionality
 */
import { z } from "zod";
import { fetchRawTicket, toCompactTicket, makeJiraRequest } from "../jira/jira-service.js";

// Utility: Extract environment details (firm, engagement, region) from any URLs in text
function extractEnvironmentDetails(text: string | undefined) {
  if (!text || typeof text !== 'string') return [] as any[];
  const urlRegex = /https?:\/\/[^\s)]+/g;
  const matches = text.match(urlRegex) || [];
  const results: any[] = [];
  for (const url of matches) {
    try {
      const u = new URL(url);
      // Region inference from host
      let region: string | undefined;
      if (/usp1/.test(u.hostname)) region = 'US Production (usp1)';
      else if (/eup1/.test(u.hostname)) region = 'Europe Production (eup1)';
      else if (/app1/.test(u.hostname)) region = 'Asia Pacific Production (app1)';
      else if (/cap1/.test(u.hostname)) region = 'Canada Production (cap1)';
      // Attempt firm & engagement extraction (path segments often contain firm/{firm}/e/eng/{engagement})
      const path = u.pathname;
      // heuristic: /{firm}/e/eng/{engagement}/ or /{firm}/e/engagement/{engagement}/
      const segments = path.split('/').filter(Boolean);
      let firm: string | undefined;
      let engagement: string | undefined;
      if (segments.length > 2) {
        firm = segments[0];
        // find engagement id (long base64-like string) by regex
        const engMatch = segments.find(s => /^[A-Za-z0-9_-]{10,}$/.test(s));
        if (engMatch) engagement = engMatch;
      }
      results.push({ url, firm, engagement, region });
    } catch (_) {
      // ignore invalid URLs
    }
  }
  return results;
}

// Utility: Suggest priority escalation based on keywords and current priority
function assessPriority(summary: string, description: string | undefined, current: string) {
  const text = (summary + ' ' + (description && typeof description === 'string' ? description : '')).toLowerCase();
  const indicators = {
    outage: /(outage|down|unreachable|downtime|service\s+down)/.test(text),
    dataLoss: /(data\s+loss|corrupt(ed)? data|lost\s+records)/.test(text),
    security: /(security|vulnerability|exploit|breach)/.test(text),
    performance: /(slow|timeout|latency|performance|degrad(ed)?)/.test(text)
  };
  let recommended = current;
  if (indicators.outage || indicators.dataLoss || indicators.security) {
    if (!/critical|blocker/i.test(current)) recommended = 'Critical';
  } else if (indicators.performance && /low|medium/i.test(current)) {
    recommended = 'High';
  }
  return { indicators, recommended };
}

// Utility: Search potential duplicates based on summary keywords (simple heuristic)
async function findPotentialDuplicates(summary: string) {
  try {
    const cleaned = summary.replace(/[^A-Za-z0-9 ]+/g, ' ').split(/\s+/).filter(w => w.length > 4).slice(0,5).join(' ');
    if (!cleaned) return [];
    const jql = `summary ~ "${cleaned}" ORDER BY updated DESC`;
    const search = await makeJiraRequest(`search?jql=${encodeURIComponent(jql)}&maxResults=5&fields=key,summary,status,priority,updated`);
    return (search.issues || []).map((i: any) => ({
      key: i.key,
      summary: i.fields.summary,
      status: i.fields.status?.name,
      priority: i.fields.priority?.name,
      updated: i.fields.updated
    }));
  } catch (e) {
    return [];
  }
}

// Utility: Build recommended labels array without duplicates
function buildRecommendedLabels(existing: string[], indicators: any, duplicatesFound: number) {
  const rec = new Set(existing);
  if (indicators.outage) rec.add('outage');
  if (indicators.dataLoss) rec.add('data-loss');
  if (indicators.security) rec.add('security-review');
  if (indicators.performance) rec.add('performance');
  if (duplicatesFound > 1) rec.add('duplicate-review');
  rec.add('ai-triaged');
  return Array.from(rec);
}

/**
 * Ticket Analysis - Root cause, impact, and timeline analysis
 */
export const ticketAnalysis = {
  name: "ticket-analysis",
  description: "Perform structured analysis on a ticket: root cause analysis, impact assessment, or timeline reconstruction",
  schema: {
    ticketId: z.string().describe("Jira ticket ID to analyze"),
    analysisType: z.enum(['root_cause', 'impact', 'timeline']).describe("Type of analysis to perform"),
    additionalContext: z.string().optional().describe("Additional context or focus areas for the analysis")
  },
  handler: async ({ ticketId, analysisType, additionalContext }: { 
    ticketId: string; 
    analysisType: 'root_cause' | 'impact' | 'timeline'; 
    additionalContext?: string 
  }) => {
    try {
      // Fetch & compact ticket data for LLM efficiency
      const raw = await fetchRawTicket(ticketId);
      const compact = toCompactTicket(raw);
      const ticketData = {
        key: compact.key,
        summary: compact.summary,
        description: compact.descriptionExcerpt,
        status: compact.status,
        priority: compact.priority,
        created: compact.created,
        updated: compact.updated,
        comments: compact.commentsExcerpt || [],
        changelog: compact.changelogExcerpt || []
      };

      let analysisPrompt = "";
      
      switch (analysisType) {
        case 'root_cause':
          analysisPrompt = `# Root Cause Analysis for ${ticketData.key}

**Ticket Summary:** ${ticketData.summary}
**Priority:** ${ticketData.priority}
**Status:** ${ticketData.status}

## Issue Description
${ticketData.description || "No description provided"}

## Analysis Framework
Please perform a root cause analysis using the 5 Whys method:

1. **What happened?** (The immediate problem)
2. **Why did it happen?** (First level cause)
3. **Why did that cause occur?** (Second level)
4. **Why did that condition exist?** (Third level)
5. **What is the root cause?** (Final answer)

## Additional Context
${additionalContext || "None provided"}

## Comments & History
${ticketData.comments.map((c: any, i: number) => `${i + 1}. ${c.a} (${c.t}): ${c.c}`).join('\n\n')}

Please provide:
- Root cause identification
- Contributing factors
- Prevention recommendations
- Related system components affected`;
          break;

        case 'impact':
          analysisPrompt = `# Impact Assessment for ${ticketData.key}

**Ticket Summary:** ${ticketData.summary}
**Priority:** ${ticketData.priority}
**Status:** ${ticketData.status}

## Issue Description
${ticketData.description || "No description provided"}

## Impact Analysis Framework
Please assess the impact across these dimensions:

### 1. Customer Impact
- Number of affected customers
- Business operations disrupted
- Revenue impact (if applicable)
- Customer satisfaction impact

### 2. System Impact
- Affected components/services
- Performance degradation
- Data integrity issues
- Security implications

### 3. Organizational Impact
- Support team workload
- Engineering resources required
- Timeline and urgency
- Reputation/PR considerations

## Additional Context
${additionalContext || "None provided"}

Please provide:
- Impact severity rating (Critical/High/Medium/Low)
- Blast radius analysis
- Mitigation priority
- Stakeholder notification needs`;
          break;

        case 'timeline':
          analysisPrompt = `# Timeline Reconstruction for ${ticketData.key}

**Ticket Summary:** ${ticketData.summary}
**Created:** ${ticketData.created}
**Last Updated:** ${ticketData.updated}

## Chronological Events

### Ticket History
${ticketData.changelog.map((h: any) => `**${h.t}** ${h.a} ${h.f}: ${h.from || '∅'} → ${h.to || '∅'}`).join('\n')}

### Comments Timeline
${ticketData.comments.map((c: any) => `**${c.created}** - ${c.author.displayName}:\n${c.body}`).join('\n\n')}

## Additional Context
${additionalContext || "None provided"}

Please reconstruct:
1. Initial incident detection
2. Key milestones and decisions
3. Response actions taken
4. Resolution timeline
5. Gaps or delays in response
6. Lessons learned for future incidents`;
          break;
      }

      return {
        content: [{
          type: "text" as const,
          text: analysisPrompt
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text" as const,
          text: `Error analyzing ticket: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};

/**
 * Knowledge Search - Search knowledge base and documentation
 */
export const knowledgeSearch = {
  name: "knowledge-search",
  description: "Structured approach to search knowledge base and documentation for troubleshooting information",
  schema: {
    topic: z.string().describe("Topic or issue to search for"),
    searchScope: z.enum(['all', 'tickets', 'documentation', 'similar_issues']).describe("Scope of search"),
    timeframe: z.string().optional().describe("Time range for search (e.g., '30d', '90d', '1y')")
  },
  handler: async ({ topic, searchScope, timeframe }: { 
    topic: string; 
    searchScope: 'all' | 'tickets' | 'documentation' | 'similar_issues'; 
    timeframe?: string 
  }) => {
    try {
      let jqlQuery = "";
      let searchDescription = "";

      switch (searchScope) {
        case 'tickets':
          jqlQuery = `text ~ "${topic}" ORDER BY updated DESC`;
          searchDescription = "Recent tickets matching your topic";
          break;
        case 'similar_issues':
          jqlQuery = `text ~ "${topic}" AND resolution != Unresolved ORDER BY resolved DESC`;
          searchDescription = "Resolved tickets with similar issues";
          break;
        case 'documentation':
          jqlQuery = `labels = "documentation" AND text ~ "${topic}"`;
          searchDescription = "Documentation tickets";
          break;
        case 'all':
        default:
          jqlQuery = `text ~ "${topic}" ORDER BY priority DESC, updated DESC`;
          searchDescription = "All related content";
          break;
      }

      // Add timeframe if specified
      if (timeframe) {
        jqlQuery += ` AND updated >= -${timeframe}`;
      }

      const searchResults = await makeJiraRequest(`search?jql=${encodeURIComponent(jqlQuery)}&maxResults=12&fields=key,summary,status,resolution,labels,updated,description`);
      const results = (searchResults.issues || []).map((issue: any) => ({
        key: issue.key,
        summary: issue.fields.summary,
        description: (issue.fields.description || "No description").slice(0,160) + (issue.fields.description && issue.fields.description.length>160?"…":""),
        status: issue.fields.status?.name || 'Unknown',
        resolution: issue.fields.resolution?.name || "Unresolved",
        labels: issue.fields.labels || [],
        updated: issue.fields.updated
      }));

      return {
        content: [{
          type: "text" as const,
          text: `# Knowledge Search Results\n\n` +
            `**Topic:** ${topic}\n` +
            `**Scope:** ${searchDescription}\n` +
            `**Results Found:** ${results.length}\n\n` +
            `---\n\n` +
            results.map((r: any, idx: number) => 
              `### ${idx + 1}. [${r.key}] ${r.summary}\n` +
              `**Status:** ${r.status} | **Resolution:** ${r.resolution}\n` +
              `**Updated:** ${r.updated}\n` +
              `**Labels:** ${r.labels.join(', ') || 'None'}\n` +
              `**Description:** ${r.description}...\n`
            ).join('\n---\n\n') +
            `\n\n**Next Steps:**\n` +
            `- Review similar tickets for solution patterns\n` +
            `- Check if any workarounds were documented\n` +
            `- Identify related components or services\n` +
            `- Look for recurring themes in resolutions`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text" as const,
          text: `Error searching knowledge base: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};

/**
 * Ticket Triage - Automated triage with priority assessment
 */
export const ticketTriage = {
  name: "ticket-triage",
  description: "Automated ticket triage with priority assessment, severity classification, and assignment recommendations",
  schema: {
    ticketId: z.string().describe("Jira ticket ID to triage"),
    includeRecommendations: z.boolean().optional().describe("Include AI-powered assignment and priority recommendations"),
    enhanced: z.boolean().optional().describe("Enable enhanced triage (environment parsing, duplicates, priority heuristics)")
  },
  handler: async ({ ticketId, includeRecommendations, enhanced }: { 
    ticketId: string; 
    includeRecommendations?: boolean;
    enhanced?: boolean;
  }) => {
    try {
      const raw = await fetchRawTicket(ticketId);
      const compact = toCompactTicket(raw);
      const ticketInfo = {
        key: compact.key,
        summary: compact.summary,
        description: compact.descriptionExcerpt,
        status: compact.status,
        priority: compact.priority,
        issueType: compact.issueType,
        labels: compact.labels,
        components: compact.components,
        reporter: compact.reporter,
        assignee: compact.assignee,
        created: compact.created,
        updated: compact.updated
      };

      // Calculate metrics
      const ageInHours = Math.floor((Date.now() - new Date(ticketInfo.created).getTime()) / (1000 * 60 * 60));
      const lastUpdateHours = Math.floor((Date.now() - new Date(ticketInfo.updated).getTime()) / (1000 * 60 * 60));

  const useEnhanced = enhanced !== false; // default true
  let triageOutput = `# Ticket Triage Report: ${ticketInfo.key}\n\n`;
      triageOutput += `## Ticket Overview\n`;
      triageOutput += `- **Summary:** ${ticketInfo.summary}\n`;
      triageOutput += `- **Type:** ${ticketInfo.issueType}\n`;
      triageOutput += `- **Current Priority:** ${ticketInfo.priority}\n`;
      triageOutput += `- **Status:** ${ticketInfo.status}\n`;
      triageOutput += `- **Reporter:** ${ticketInfo.reporter}\n`;
      triageOutput += `- **Assignee:** ${ticketInfo.assignee}\n\n`;

      triageOutput += `## Triage Metrics\n`;
      triageOutput += `- **Age:** ${ageInHours} hours (${Math.floor(ageInHours / 24)} days)\n`;
      triageOutput += `- **Last Update:** ${lastUpdateHours} hours ago\n`;
      triageOutput += `- **Components:** ${ticketInfo.components.join(', ') || 'None specified'}\n`;
      triageOutput += `- **Labels:** ${ticketInfo.labels.join(', ') || 'None'}\n\n`;

      // Priority indicators
      triageOutput += `## Priority Indicators\n`;
      const priorityIndicators: string[] = [];

      const priorityAssessment = useEnhanced ? assessPriority(ticketInfo.summary, ticketInfo.description, ticketInfo.priority) : { indicators: {}, recommended: ticketInfo.priority };
      if (/Critical|Blocker/i.test(ticketInfo.priority)) {
        priorityIndicators.push('🔴 High priority ticket - immediate attention required');
      }
      if (ticketInfo.assignee === 'Unassigned') {
        priorityIndicators.push('⚠️ Unassigned - needs owner');
      }
      if (ageInHours > 72) {
        priorityIndicators.push('⏰ Aging ticket - review required');
      }
      if (lastUpdateHours > 48) {
        priorityIndicators.push('📌 Stale - no recent updates');
      }
      if (ticketInfo.labels.includes('customer-facing')) {
        priorityIndicators.push('👥 Customer-facing impact');
      }
      if (useEnhanced) {
        const { indicators, recommended } = priorityAssessment as any;
        if ((indicators.outage || indicators.dataLoss || indicators.security) && recommended !== ticketInfo.priority) {
          priorityIndicators.push(`⬆️ Recommended priority escalation to **${recommended}** based on detected critical indicators`);
        }
      }
      triageOutput += priorityIndicators.length ? priorityIndicators.map(i => `- ${i}`).join('\n') + '\n\n' : '- ✅ No critical indicators detected\n\n';

      // Description analysis
      triageOutput += `## Issue Description\n${ticketInfo.description || 'No description provided'}\n\n`;

      // Enhanced sections
      if (useEnhanced) {
        const envDetails = extractEnvironmentDetails(ticketInfo.description || '') || [];
        if (envDetails.length) {
          triageOutput += `## Environment Details (Extracted)\n`;
          envDetails.forEach((d, idx) => {
            triageOutput += `- URL ${idx + 1}: ${d.url}\n  - Firm: ${d.firm || 'Unknown'}\n  - Engagement: ${d.engagement || 'Unknown'}\n  - Region: ${d.region || 'Unknown'}\n`;
          });
          triageOutput += '\n';
        }
        // Potential duplicates
        const duplicates = await findPotentialDuplicates(ticketInfo.summary);
        if (duplicates.length) {
          triageOutput += `## Potential Duplicates (Top ${duplicates.length})\n`;
          duplicates.forEach((d: { key: string; status: string; priority: string; summary: string; updated: string; }) => {
            triageOutput += `- ${d.key} | ${d.status} | ${d.priority} | ${d.summary} (Updated: ${d.updated})\n`;
          });
          triageOutput += '\n';
        }
      }

      if (includeRecommendations) {
        triageOutput += `## Triage Recommendations\n\n`;
        triageOutput += `### Suggested Actions:\n`;

        let actionIndex = 1;
        if (ticketInfo.assignee === 'Unassigned') {
          triageOutput += `${actionIndex++}. **Assignment Needed:** Review components (${ticketInfo.components.join(', ') || 'none'}) to identify appropriate team/engineer\n`;
        }
        if (useEnhanced && (priorityAssessment as any).recommended !== ticketInfo.priority) {
          triageOutput += `${actionIndex++}. **Priority Escalation:** Recommend updating priority to ${(priorityAssessment as any).recommended}\n`;
        }
        if (ageInHours > 24 && /Critical/i.test(ticketInfo.priority)) {
          triageOutput += `${actionIndex++}. **SLA Risk:** Critical ticket open for ${Math.floor(ageInHours / 24)} days - may breach SLA\n`;
        }
        if (!ticketInfo.description || ticketInfo.description.length < 50) {
          triageOutput += `${actionIndex++}. **Information Gap:** Limited description - request additional details from reporter\n`;
        }
        if (useEnhanced) {
          triageOutput += `${actionIndex++}. **Add Labels:** ${buildRecommendedLabels(ticketInfo.labels, (priorityAssessment as any).indicators || {}, 0).join(', ')}\n`;
        }

        triageOutput += `\n### Next Steps Checklist:\n`;
        triageOutput += `- [ ] Verify / adjust priority\n`;
        triageOutput += `- [ ] Assign owner\n`;
        triageOutput += `- [ ] Confirm environment & engagement details\n`;
        triageOutput += `- [ ] Gather missing technical data (logs, versions)\n`;
        triageOutput += `- [ ] Communicate status to stakeholders\n`;
        triageOutput += `- [ ] Plan mitigation / resolution path\n`;
      }

      return {
        content: [{
          type: "text" as const,
          text: triageOutput
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text" as const,
          text: `Error performing triage: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};

/**
 * Support Automation Service - Unified export
 */
export const supportAutomationService = {
  ticketAnalysis,
  knowledgeSearch,
  ticketTriage
};

// Export individual tools for backward compatibility
export const ticketAnalysisTool = ticketAnalysis;
export const knowledgeSearchTool = knowledgeSearch;
export const ticketTriageTool = ticketTriage;
