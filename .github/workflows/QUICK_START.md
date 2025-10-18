# Dev ? Main Sync Workflow Quick Reference

## ?? Quick Start

You now have **two workflow options** for syncing `dev` to `main`:

### Option 1: Basic Auto-Sync (Recommended for Most Projects)
**File**: `.github/workflows/sync-dev-to-main.yml`

**Features:**
- ? Automatic sync when PR to `dev` is merged
- ? Merge commit with PR reference
- ? PR comments on success/failure
- ? Simple and reliable

**Use when:** You trust your dev branch and want simple automation

### Option 2: Enhanced with Validation
**File**: `.github/workflows/sync-dev-to-main-enhanced.yml`

**Features:**
- ? All basic features PLUS:
- ? Requires at least 1 approval
- ? Can skip with `no-sync` or `hold` labels
- ? Checks CI status before sync
- ? Creates backup tags
- ? Post-merge validation hooks
- ? Slack notification support (optional)

**Use when:** You need extra safety checks and control

## ?? Setup Checklist

### 1. Choose Your Workflow
```bash
# Use basic version (most projects)
git add .github/workflows/sync-dev-to-main.yml

# OR use enhanced version (production/critical projects)
git add .github/workflows/sync-dev-to-main-enhanced.yml

# Commit and push
git commit -m "feat: add dev to main auto-sync workflow"
git push origin dev
```

### 2. Configure Branch Protection (Important!)

Go to: **Settings** ? **Branches** ? **Add rule** for `main`

Required settings:
- ? **Require pull request reviews** (at least 1)
- ? **Require status checks to pass**
- ?? **Allow GitHub Actions to bypass** (for auto-sync to work)

### 3. Test the Workflow

1. Create a test branch from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b test/workflow-sync
   echo "Test sync workflow" >> README.md
   git add README.md
   git commit -m "test: verify auto-sync workflow"
   git push origin test/workflow-sync
   ```

2. Create PR to `dev` branch

3. Get it reviewed and approved

4. Merge the PR

5. Check **Actions** tab ? "Sync Dev to Main" workflow

6. Verify `main` branch was updated

## ?? Common Workflows

### Standard Development Flow
```
???????????????
?   feature   ????????
?   branch    ?      ? PR ? dev
???????????????      ?
                ???????????????      Auto-sync
                ?     dev     ?????????????????????????????????
                ?   (testing) ?                 ?    main     ?
                ???????????????                 ?  (stable)   ?
                                                ???????????????
```

**Steps:**
1. Create feature branch from `dev`
2. Develop and commit changes
3. Open PR: `feature` ? `dev`
4. Review, approve, merge
5. **? Auto-sync: `dev` ? `main`**

### Hotfix to Production
```
???????????????
?   hotfix    ????????
?   branch    ?      ? PR ? main (manual)
???????????????      ?
                ???????????????
                ?    main     ?
                ?  (updated)  ?
                ???????????????
                      ?
                      ? PR ? dev (to backport)
                      ?
                ???????????????
                ?     dev     ?
                ???????????????
```

**Steps:**
1. Create hotfix from `main`
2. Fix the issue
3. Open PR: `hotfix` ? `main` (manual merge, bypass auto-sync)
4. Create backport PR: `main` ? `dev`

## ??? Special Labels

### Skip Auto-Sync
Add label to PR **before merging**: `no-sync` or `hold`

**Use cases:**
- Breaking changes need manual verification
- Waiting for dependent services
- Coordinated release required

### Manual Sync Later
```bash
# After fixing issues or coordination
git checkout main
git merge dev
git push origin main
```

## ?? Monitoring & Troubleshooting

### Check Workflow Status
1. Go to repository ? **Actions** tab
2. Look for "Sync Dev to Main" workflow
3. Click on specific run to see logs

### Common Issues

#### ? "Merge Conflict"
**Symptom:** Workflow fails with conflict message

**Solution:**
```bash
git checkout main
git pull origin main
git merge dev
# Resolve conflicts in your editor
git add .
git commit
git push origin main
```

#### ? "Permission Denied"
**Symptom:** Can't push to main

**Solution:** Configure branch protection to allow GitHub Actions:
1. Settings ? Branches ? main rule
2. Add `github-actions[bot]` to bypass list

#### ? "Workflow Not Triggering"
**Symptom:** PR merged but workflow didn't run

**Checklist:**
- ? Workflow file in `.github/workflows/`?
- ? PR was to `dev` branch?
- ? PR was merged (not closed)?
- ? Check Actions tab for any errors

## ??? Customization Examples

### Require 2 Approvals
Edit workflow, add to `pre-sync-validation` job:
```yaml
- name: Require minimum approvals
  run: |
    if [ ${{ steps.check_approvals.outputs.approval_count }} -lt 2 ]; then
      echo "Minimum 2 approvals required"
      exit 1
    fi
```

### Only Sync on Specific Days
Add to job condition:
```yaml
jobs:
  sync-to-main:
    if: |
      github.event.pull_request.merged == true &&
      contains(fromJSON('["Monday","Wednesday","Friday"]'), 
               format('{0:dddd}', github.event.pull_request.merged_at))
```

### Run Tests Before Sync
Add step before push:
```yaml
- name: Run tests
  run: |
    npm test  # or your test command
```

## ?? Get Help

### Workflow Not Working?
1. Check workflow logs in Actions tab
2. Review this guide
3. Check [GitHub Actions docs](https://docs.github.com/en/actions)

### Need to Rollback?
```bash
# Find backup tag (enhanced workflow creates these)
git tag | grep backup-main

# Rollback main to backup
git checkout main
git reset --hard backup-main-20241225-120000
git push --force origin main
```

### Questions?
- Read full guide: `.github/workflows/SYNC_WORKFLOW_GUIDE.md`
- Open an issue in the repository
- Contact repository maintainer

---

## ?? You're All Set!

The workflow is ready to use. Just merge PRs to `dev` as usual, and `main` will stay in sync automatically!

**First time?** Test with a small PR to verify everything works correctly.

---

*Last updated: 2024 | Workflow version: 1.0.0*
