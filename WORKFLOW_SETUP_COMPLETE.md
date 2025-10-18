# ? Dev ? Main Auto-Sync Workflow Setup Complete!

## ?? What Was Created

Your repository now has automatic synchronization from `dev` to `main` branch! Here's what was added:

### ?? Files Added

1. **`.github/workflows/sync-dev-to-main.yml`** ? **RECOMMENDED**
   - Basic auto-sync workflow
   - Merges `dev` ? `main` when PR is merged
   - Posts comments on success/failure
   - Simple and reliable

2. **`.github/workflows/sync-dev-to-main-enhanced.yml`**
   - Advanced workflow with safety checks
   - Requires at least 1 approval
   - Checks CI status
   - Creates backup tags
   - Can skip sync with labels
   - Best for production/critical projects

3. **`.github/workflows/SYNC_WORKFLOW_GUIDE.md`**
   - Complete documentation
   - Configuration examples
   - Troubleshooting guide
   - Security best practices

4. **`.github/workflows/QUICK_START.md`**
   - Quick reference guide
   - Setup checklist
   - Common workflows
   - Troubleshooting tips

## ?? How It Works

```
Developer Workflow:
???????????????
?   Create    ?
?  feature    ?
?   branch    ?
???????????????
       ?
       ?
???????????????
?  Open PR    ?
?  to  dev    ?
???????????????
       ?
       ?
???????????????
?   Review    ?
?  & Approve  ?
???????????????
       ?
       ?
???????????????
?  Merge PR   ?
?   to dev    ?
???????????????
       ?
       ?
???????????????
?? AUTO-SYNC ?  ? GitHub Actions Workflow
?  dev ? main ?
???????????????
```

## ?? Next Steps

### 1. Choose Your Workflow (Pick One)

**For most projects** (recommended):
```bash
# Use: .github/workflows/sync-dev-to-main.yml
# Already active! No action needed.
```

**For critical/production projects**:
```bash
# Option A: Rename enhanced to be primary
git mv .github/workflows/sync-dev-to-main.yml .github/workflows/sync-dev-to-main-basic.yml
git mv .github/workflows/sync-dev-to-main-enhanced.yml .github/workflows/sync-dev-to-main.yml

# Option B: Delete basic and rename enhanced
git rm .github/workflows/sync-dev-to-main.yml
git mv .github/workflows/sync-dev-to-main-enhanced.yml .github/workflows/sync-dev-to-main.yml

git commit -m "chore: switch to enhanced auto-sync workflow"
git push origin dev
```

### 2. Configure Branch Protection for `main`

?? **IMPORTANT**: This is required for the workflow to work!

1. Go to: **https://github.com/leonxuecloud/Agentic-AI-Experiment/settings/branches**

2. Click **"Add branch protection rule"**

3. Branch name pattern: `main`

4. Enable these settings:
   - ? **Require a pull request before merging**
   - ? **Require approvals** (at least 1)
   - ? **Require status checks to pass before merging**
   - ? **Do not allow bypassing the above settings**

5. **Important**: Under "Rules applied to everyone including administrators"
   - Add exception: Allow `github-actions[bot]` to bypass
   - OR: In workflow settings, use a Personal Access Token (PAT) with admin rights

6. Click **"Create"**

### 3. Test the Workflow

Create a test PR to verify everything works:

```bash
# On dev branch
git checkout dev
git pull origin dev

# Create test branch
git checkout -b test/auto-sync-verification

# Make a small change
echo "Testing auto-sync workflow" >> test-file.txt
git add test-file.txt
git commit -m "test: verify auto-sync workflow"
git push origin test/auto-sync-verification

# Now on GitHub:
# 1. Create PR: test/auto-sync-verification ? dev
# 2. Review and approve
# 3. Merge the PR
# 4. Go to Actions tab
# 5. Watch "Sync Dev to Main" workflow run
# 6. Verify main branch was updated
```

## ?? Monitoring

### View Workflow Runs
- **Actions Tab**: https://github.com/leonxuecloud/Agentic-AI-Experiment/actions
- Look for "Sync Dev to Main" workflow
- Check run history and logs

### Notifications
- GitHub will comment on each PR with sync status
- Email notifications on workflow failures
- (Optional) Configure Slack notifications in enhanced workflow

## ?? Workflow Features

### Basic Workflow
- ? Auto-merge when PR to `dev` is merged
- ? Creates merge commit with PR reference
- ? Posts success/failure comments on PR
- ? Simple error handling

### Enhanced Workflow
- ? All basic features PLUS:
- ? Pre-sync validation (approvals, labels)
- ? CI status checks
- ? Automatic backup tags before sync
- ? Post-merge validation hooks
- ? Skip sync with `no-sync` or `hold` labels
- ? Detailed status reporting

## ?? Customization

### Skip Auto-Sync for Specific PR
Add label before merging: `no-sync` or `hold`

### Require More Approvals
Edit workflow file, modify approval check:
```yaml
# Change from 1 to desired number
if (approvals.length < 2) {
  core.setFailed('At least 2 approvals required');
}
```

### Add Slack Notifications
Uncomment Slack step in enhanced workflow and add secret:
```bash
# In GitHub: Settings ? Secrets ? Actions ? New repository secret
# Name: SLACK_WEBHOOK_URL
# Value: <your-webhook-url>
```

## ?? Troubleshooting

### Workflow Not Running?
1. Check workflow file is in `.github/workflows/`
2. Verify PR was to `dev` branch
3. Confirm PR was merged (not closed)
4. Check Actions tab for errors

### Permission Errors?
1. Verify `contents: write` permission in workflow
2. Check branch protection allows GitHub Actions
3. Consider using PAT instead of GITHUB_TOKEN

### Merge Conflicts?
The workflow will fail and post a comment. Manual resolution:
```bash
git checkout main
git pull origin main
git merge dev
# Resolve conflicts
git commit
git push origin main
```

## ?? Documentation

- **Quick Start**: `.github/workflows/QUICK_START.md`
- **Full Guide**: `.github/workflows/SYNC_WORKFLOW_GUIDE.md`
- **Basic Workflow**: `.github/workflows/sync-dev-to-main.yml`
- **Enhanced Workflow**: `.github/workflows/sync-dev-to-main-enhanced.yml`

## ?? Best Practices

1. ? **Test in dev first** - All features thoroughly tested
2. ? **Small PRs** - Easier to review and sync
3. ? **Clear commit messages** - Understand what's being synced
4. ? **Monitor workflows** - Check Actions tab regularly
5. ? **Keep main stable** - Only merge tested code

## ?? Important Notes

### Current Status
- ? Workflows committed to `dev` branch
- ? Pushed to GitHub
- ?? **Not yet active** - Waiting for branch protection configuration
- ?? **Needs testing** - Create test PR to verify

### Before Production Use
1. [ ] Configure branch protection on `main`
2. [ ] Test with sample PR
3. [ ] Verify sync works as expected
4. [ ] Train team on new workflow
5. [ ] Document any custom modifications

## ?? Tips

- The workflow only runs when PR is **merged**, not closed
- Both `dev` and `main` must exist in repository
- Workflow uses merge commit (not fast-forward) for better history
- Backup tags are created in enhanced workflow (safe rollback)
- PR comments provide immediate feedback

## ?? You're Ready!

The auto-sync workflow is set up and ready to use. Just configure branch protection and test with a PR!

**Questions?** Check the documentation or open an issue.

---

**Setup Date**: January 2025
**Repository**: leonxuecloud/Agentic-AI-Experiment
**Branch**: dev
**Workflow Version**: 1.0.0

? Happy coding with automated branch syncing! ?
