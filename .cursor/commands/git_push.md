---
description: Stages all changes, generates a commit message, commits locally, and pushes to the current remote branch.
---

# Git Add, Commit, and Push

The agent will perform the following sequence of actions:

1.  **Stage all changes:** Run `git add --all` in the terminal to prepare all modified, new, and deleted files for the commit.
2.  **Generate Commit Message:** Use Cursor's built-in AI feature to generate a concise and descriptive commit message based on the staged changes.
3.  **Commit Locally:** Commit the staged files using the generated message. For example: `git commit -m "Generated commit message here"`
4.  **Push to GitHub:** Push the committed changes to the configured remote repository (GitHub) and the current branch using `git push origin <current-branch-name>`.

The agent should confirm the process is complete and report any errors encountered during the terminal commands.
