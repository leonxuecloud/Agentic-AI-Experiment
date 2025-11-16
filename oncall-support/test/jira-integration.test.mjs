/**
 * Jira Integration Tests - Live Tests for Triage Workflow
 * 
 * Tests:
 * 1. Triage analysis with recommendations
 * 2. Simple public comment
 * 3. Full triage workflow (comment, labels, transitions)
 * 
 * Usage:
 *   node test/jira-integration.test.mjs [test-name]
 * 
 * Examples:
 *   node test/jira-integration.test.mjs triage
 *   node test/jira-integration.test.mjs comment
 *   node test/jira-integration.test.mjs workflow
 *   node test/jira-integration.test.mjs all
 */

import { config } from 'dotenv';
config();

import { ticketTriageTool } from '../dist/tools/support-automation/support-automation-service.js';
import { addJiraCommentTool, updateJiraFieldsTool, getJiraTransitionsTool } from '../dist/tools/jira/jira-service.js';

// Test configuration
const TEST_TICKET_ID = process.env.TEST_TICKET_ID || 'AI-896';

/**
 * Test 1: Enhanced triage analysis
 */
async function testTriageAnalysis() {
  console.log('='.repeat(60));
  console.log('Test 1: Triage Analysis with Recommendations');
  console.log('='.repeat(60));
  console.log(`Testing ticket: ${TEST_TICKET_ID}\n`);

  try {
    const result = await ticketTriageTool.handler({ 
      ticketId: TEST_TICKET_ID, 
      includeRecommendations: true 
    });
    console.log(result.content[0].text);
    console.log('\n✅ Triage analysis test PASSED\n');
    return true;
  } catch (error) {
    console.error('❌ Triage analysis test FAILED:', error.message);
    console.error('Stack:', error.stack);
    return false;
  }
}

/**
 * Test 2: Simple public comment
 */
async function testSimpleComment() {
  console.log('='.repeat(60));
  console.log('Test 2: Simple Public Comment');
  console.log('='.repeat(60));
  console.log(`Testing ticket: ${TEST_TICKET_ID}\n`);

  try {
    const timestamp = new Date().toISOString();
    const result = await addJiraCommentTool.handler({
      ticketId: TEST_TICKET_ID,
      body: `🤖 Automated test comment - ${timestamp}\n\nThis is a test of the MCP server's comment functionality.`
    });
    console.log(result.content[0].text);
    console.log('\n✅ Simple comment test PASSED\n');
    return true;
  } catch (error) {
    console.error('❌ Simple comment test FAILED:', error.response?.data || error.message);
    return false;
  }
}

/**
 * Test 3: Full triage workflow
 */
async function testFullTriageWorkflow() {
  console.log('='.repeat(60));
  console.log('Test 3: Full Triage Workflow');
  console.log('='.repeat(60));
  console.log(`Testing ticket: ${TEST_TICKET_ID}\n`);

  let passed = true;

  // Step 1: Add triage comment (public - no visibility restrictions)
  console.log('📝 Step 1: Adding triage comment...\n');
  try {
    const commentResult = await addJiraCommentTool.handler({
      ticketId: TEST_TICKET_ID,
      body: '🤖 Automated Triage Analysis\n\n' +
            'Priority Assessment: Ticket requires attention.\n' +
            'Recommendation: Review and assign to appropriate team member.\n' +
            'Labels: ai-triaged, needs-review'
    });
    console.log(commentResult.content[0].text);
    console.log('✅ Comment step PASSED\n');
  } catch (error) {
    console.error('❌ Comment step FAILED:', error.response?.data || error.message);
    passed = false;
  }

  // Step 2: Update fields (add labels)
  console.log('🏷️  Step 2: Adding labels...\n');
  try {
    const updateResult = await updateJiraFieldsTool.handler({
      ticketId: TEST_TICKET_ID,
      updates: {
        labels: ['AI_-_Story_-_Definition_of_Done', 'ai-triaged', 'needs-review']
      }
    });
    console.log(updateResult.content[0].text);
    console.log('✅ Label update step PASSED\n');
  } catch (error) {
    console.error('❌ Label update step FAILED:', error.response?.data || error.message);
    passed = false;
  }

  // Step 3: Get available transitions
  console.log('🔄 Step 3: Checking available transitions...\n');
  try {
    const transitionsResult = await getJiraTransitionsTool.handler({ ticketId: TEST_TICKET_ID });
    console.log(transitionsResult.content[0].text);
    console.log('✅ Transitions step PASSED\n');
  } catch (error) {
    console.error('❌ Transitions step FAILED:', error.response?.data || error.message);
    passed = false;
  }

  console.log('='.repeat(60));
  if (passed) {
    console.log('✅ Full workflow test PASSED');
  } else {
    console.log('❌ Full workflow test FAILED (see errors above)');
  }
  console.log('='.repeat(60));
  console.log();

  return passed;
}

/**
 * Run all tests
 */
async function runAllTests() {
  console.log('\n🚀 Running All Jira Integration Tests\n');
  
  const results = {
    triage: await testTriageAnalysis(),
    comment: await testSimpleComment(),
    workflow: await testFullTriageWorkflow()
  };

  console.log('='.repeat(60));
  console.log('📊 Test Summary');
  console.log('='.repeat(60));
  console.log(`Triage Analysis:    ${results.triage ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`Simple Comment:     ${results.comment ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`Full Workflow:      ${results.workflow ? '✅ PASSED' : '❌ FAILED'}`);
  console.log('='.repeat(60));
  
  const allPassed = Object.values(results).every(r => r);
  console.log(`\n${allPassed ? '✅ All tests PASSED' : '❌ Some tests FAILED'}\n`);
  
  process.exit(allPassed ? 0 : 1);
}

/**
 * Main entry point
 */
async function main() {
  const testName = process.argv[2] || 'all';

  switch (testName.toLowerCase()) {
    case 'triage':
      await testTriageAnalysis();
      break;
    case 'comment':
      await testSimpleComment();
      break;
    case 'workflow':
      await testFullTriageWorkflow();
      break;
    case 'all':
      await runAllTests();
      break;
    default:
      console.error(`❌ Unknown test: ${testName}`);
      console.error('Available tests: triage, comment, workflow, all');
      process.exit(1);
  }
}

main();
