---
name: auto-release
description: >-
  Use this skill whenever the user approves code changes, edits, or fixes, or asks to
  release, publish, tag, or create a GitHub release for NeptunSmart.
---

# Auto Release Workflow

This skill automates the process of tagging and releasing updates for the NeptunSmart Home Assistant integration on GitHub upon user approval.

## Requirements

1. **GitHub CLI (`gh`)**: `/opt/homebrew/bin/gh` or `gh` in PATH, authenticated with GitHub credentials.
2. **Git permissions**: Working branch should be `main` and up to date with `origin`.
3. **Sandbox elevation**: Commands involving `git push` or `gh release create` interact with the network and external keychain; use `BypassSandbox: true` when running them.

---

## Workflow Steps

When the user approves a change (e.g. "утверждаю", "применяем", "выпускай релиз", "сделай релиз"):

### 1. Determine the New Version
* Read current version from `custom_components/neptun_smart_local/manifest.json`.
* Determine semantic bump:
  * **Patch** (e.g. `0.7.1` -> `0.7.2`): Bug fixes, translations, minor config improvements.
  * **Minor** (e.g. `0.7.1` -> `0.8.0`): New features, new entities, significant functionality additions.
  * Or use a specific version explicitly requested by the user.

### 2. Verify Manifest and HACS Requirements
* Ensure `hacs.json` exists in repository root:
  ```json
  {
    "name": "Neptun Smart",
    "render_readme": true
  }
  ```
* Ensure `custom_components/neptun_smart_local/manifest.json` has:
  * `"version": "<new_version>"`
  * `"issue_tracker": "https://github.com/titovskiy/NeptunSmart/issues"`

### 3. Execute Release
Use the helper script [release.sh](./scripts/release.sh) or execute the steps manually:

```bash
# Using the helper script:
./.agents/skills/auto-release/scripts/release.sh <version> "<title>" "<notes>"
```

Or manually:
```bash
# 1. Stage and commit
git add -u
git commit -m "Release v<version>: <summary>"

# 2. Push main
git push origin main

# 3. Create and push annotated tag
git tag -a "v<version>" -m "Release v<version>: <summary>"
git push origin "v<version>"

# 4. Create GitHub Release
/opt/homebrew/bin/gh release create "v<version>" \
  --title "Neptun Smart v<version>" \
  --notes "<changelog notes>"
```

### 4. Provide Feedback
* Output the direct link to the new GitHub Release:
  `https://github.com/titovskiy/NeptunSmart/releases/tag/v<version>`
* Remind the user that Home Assistant Marketplace / HACS will detect the new release upon checking for updates.
