/**
 * Tools Registry - Central export for all MCP tools
 * 
 * Tools are organized into categories:
 * - JIRA Integration: Ticket operations and search
 * - File Operations: File management and extraction
 * - Support Automation: Analysis, triage, and knowledge search
 */

// JIRA Integration Tools
export { getJiraTicketTool, searchJiraTicketsTool } from "./jira/index.js";

// File Operations Tools (can be enabled/disabled via configuration)
export { 
  downloadFileTool, 
  extractZipTool, 
  listLocalFilesTool, 
  readLocalFileTool 
} from "./file-operations/index.js";

// Support Automation Tools
export { 
  ticketAnalysisTool, 
  knowledgeSearchTool, 
  ticketTriageTool 
} from "./support-automation/index.js";

/**
 * Tool categories for conditional registration
 */
export const toolCategories = {
  jira: ['getJiraTicketTool', 'searchJiraTicketsTool'],
  fileOps: ['downloadFileTool', 'extractZipTool', 'listLocalFilesTool', 'readLocalFileTool'],
  supportAutomation: ['ticketAnalysisTool', 'knowledgeSearchTool', 'ticketTriageTool']
};
