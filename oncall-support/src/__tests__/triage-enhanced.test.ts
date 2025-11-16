import { describe, it, expect } from 'vitest';
import { ticketTriageTool } from '../tools/support-automation/support-automation-service.js';
import * as JiraSvc from '../tools/jira/jira-service.js';

// NOTE: Lightweight test: we override network-dependent helpers with local mocks using Object.defineProperty
// because original exports are read-only. This avoids needing real Jira credentials.

// Minimal raw ticket stub
const rawTicket = {
  key: 'PROD-999',
  fields: {
    summary: 'Production outage causing database timeouts',
    description: 'Customer reports outage. URL: https://nl.usp1.casewarecloud.com/firma/e/eng/bCE9KJbxSv6wu2118IE58g/index.jsp#/documents',
    issuetype: { name: 'Bug' },
    priority: { name: 'Medium' },
    status: { name: 'New' },
    labels: ['customer-facing'],
    components: [{ name: 'Backend' }],
    reporter: { displayName: 'Alice Reporter' },
    assignee: null,
    created: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5h ago
    updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2h ago
  },
  changelog: { histories: [] },
  comments: { comments: [] }
} as any;

// Monkey patch imported helpers by editing module namespace (works since we use JS emits)
// Instead of monkey patching read-only exports, create lightweight inlined substitutes by temporarily
// injecting into the global module cache using dynamic import override via a local shim.
// For simplicity, we simulate the triage output by invoking the tool with real code while
// intercepting network helpers through a manual mock object passed via globalThis.

// Override helpers
Object.defineProperty(JiraSvc, 'fetchRawTicket', { value: async () => rawTicket });
Object.defineProperty(JiraSvc, 'toCompactTicket', { value: (r: any) => ({
  key: r.key,
  summary: r.fields.summary,
  descriptionExcerpt: r.fields.description,
  status: r.fields.status.name,
  priority: r.fields.priority.name,
  issueType: r.fields.issuetype.name,
  labels: r.fields.labels,
  components: r.fields.components.map((c: any) => c.name),
  reporter: r.fields.reporter.displayName,
  assignee: r.fields.assignee?.displayName || 'Unassigned',
  created: r.fields.created,
  updated: r.fields.updated
}) });
Object.defineProperty(JiraSvc, 'makeJiraRequest', { value: async () => ({ issues: [ { key: 'PROD-998', fields: { summary: 'Production outage affecting cache layer', status: { name: 'Open' }, priority: { name: 'High' }, updated: new Date().toISOString() } } ] }) });

describe('Enhanced Ticket Triage', () => {
  it('should include environment details, priority escalation recommendation and duplicate section', async () => {
  const result = await ticketTriageTool.handler({ ticketId: 'PROD-999', includeRecommendations: true });
    const text = result.content[0].text;
    expect(text).toMatch(/Environment Details/);
    expect(text).toMatch(/Recommended priority escalation/);
    expect(text).toMatch(/Potential Duplicates/);
  expect(text).toMatch(/Add Labels:/);
    expect(text).toMatch(/ai-triaged/);
  });

  it('should allow basic mode without enhanced sections', async () => {
  const result = await ticketTriageTool.handler({ ticketId: 'PROD-999', enhanced: false });
    const text = result.content[0].text;
    expect(text).not.toMatch(/Environment Details/);
    expect(text).not.toMatch(/Potential Duplicates/);
  });
});
