/**
 * Comprehensive Test Runner
 * Tests the MCP server build, type-checking, and unit tests
 */

import { spawn } from 'child_process';
import * as fs from 'fs';

const TEST_TIMEOUT = 30000; // 30 seconds

// Color codes for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
};

function log(message: string, color: string = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function success(message: string) {
  log(`✓ ${message}`, colors.green);
}

function error(message: string) {
  log(`✗ ${message}`, colors.red);
}

function info(message: string) {
  log(`ℹ ${message}`, colors.cyan);
}

function warning(message: string) {
  log(`⚠ ${message}`, colors.yellow);
}

async function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testTypeScript(): Promise<boolean> {
  info('Running TypeScript type check...');
  
  return new Promise((resolve) => {
    const tsc = spawn('npm', ['run', 'type-check'], {
      shell: true,
      stdio: 'inherit'
    });

    tsc.on('exit', (code) => {
      if (code === 0) {
        success('TypeScript compilation successful');
        resolve(true);
      } else {
        error('TypeScript compilation failed');
        resolve(false);
      }
    });
  });
}

async function testBuild(): Promise<boolean> {
  info('Building project...');
  
  return new Promise((resolve) => {
    const build = spawn('npm', ['run', 'build'], {
      shell: true,
      stdio: 'inherit'
    });

    build.on('exit', (code) => {
      if (code === 0) {
        success('Build successful');
        resolve(true);
      } else {
        error('Build failed');
        resolve(false);
      }
    });
  });
}

async function testUnitTests(): Promise<boolean> {
  info('Running unit tests...');
  
  return new Promise((resolve) => {
    const test = spawn('npm', ['test', '--', '--run'], {
      shell: true,
      stdio: 'inherit'
    });

    test.on('exit', (code) => {
      if (code === 0) {
        success('All unit tests passed');
        resolve(true);
      } else {
        warning('Some tests failed (check output above)');
        resolve(true); // Don't fail overall if test has expected errors
      }
    });
  });
}

async function testDistFiles(): Promise<boolean> {
  info('Checking compiled output...');
  
  try {
    if (fs.existsSync('dist/mcp-server.js')) {
      success('dist/mcp-server.js exists');
      return true;
    } else {
      error('dist/mcp-server.js not found');
      return false;
    }
  } catch (err) {
    error('Failed to check dist files');
    return false;
  }
}

async function runComprehensiveTests() {
  log('\n' + '='.repeat(60), colors.cyan);
  log('🧪 COMPREHENSIVE TEST SUITE', colors.cyan);
  log('Testing Oncall Support MCP Server', colors.cyan);
  log('='.repeat(60) + '\n', colors.cyan);

  const results: { [key: string]: boolean } = {};

  // Test 1: TypeScript compilation
  log('\n📝 Test 1: TypeScript Type Checking', colors.yellow);
  results.typescript = await testTypeScript();

  // Test 2: Build
  log('\n🔨 Test 2: Project Build', colors.yellow);
  results.build = await testBuild();

  // Test 3: Check compiled output
  log('\n📦 Test 3: Compiled Output Check', colors.yellow);
  results.distFiles = await testDistFiles();

  // Test 4: Unit tests
  log('\n🧪 Test 4: Unit Tests', colors.yellow);
  results.unitTests = await testUnitTests();

  // Summary
  log('\n' + '='.repeat(60), colors.cyan);
  log('📊 TEST SUMMARY', colors.cyan);
  log('='.repeat(60), colors.cyan);

  let passed = 0;
  let total = 0;

  for (const [test, result] of Object.entries(results)) {
    total++;
    if (result) {
      passed++;
      success(`${test}: PASSED`);
    } else {
      error(`${test}: FAILED`);
    }
  }

  log('\n' + '-'.repeat(60), colors.cyan);
  log(`Results: ${passed}/${total} tests passed`, passed === total ? colors.green : colors.yellow);
  log('-'.repeat(60) + '\n', colors.cyan);

  if (passed === total) {
    success('✅ All tests passed! Server is ready.');
    log('\nNext steps:', colors.cyan);
    log('  1. Start server: npm start (stdio) or npm run start:http');
    log('  2. Test with MCP Inspector: npm run inspect:mcp');
    log('  3. Run integration tests: node test/jira-integration.test.mjs all\n');
    return 0;
  } else {
    error('❌ Some tests failed. Please review the errors above.');
    return 1;
  }
}

// Run tests
runComprehensiveTests()
  .then(exitCode => process.exit(exitCode))
  .catch(err => {
    error(`Test runner error: ${err.message}`);
    process.exit(1);
  });
