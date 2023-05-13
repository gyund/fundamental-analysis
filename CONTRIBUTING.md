# How to Contribute

First off, thank you for contributing! We're excited to collaborate with you! 🎉

The following is a set of guidelines for the many ways you can join our collective effort.

Before anything else, please take a moment to read our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all participants, from full-timers to occasional tinkerers, to uphold it.

## Reporting Bugs, Asking Questions, and Suggesting Features

Have a suggestion or feedback? Please go to [Issues](https://github.com/gyund/fundamental-analysis/issues) and [open a new issue](https://github.com/gyund/fundamental-analysis/issues/new). Prefix the title with a category like _"Bug:"_, _"Question:"_, or _"Feature Request:"_. Screenshots help us resolve issues and answer questions faster, so thanks for including some if you can.

## Submitting Code Changes

If you plan to work on an issue, please indicate in the comments of the issue that you plan to work on it. This helps avoid anyone from spending time duplicating efforts to solve a particular problem. It happens, but we certainly don't want to waste anyone's time. Ask for clarification if there's things about the issue that aren't clear. 

When submitting changes, we use black and isort to keep our code clean. Please run `./autoformat.sh` in the project directory to cleanup code before submitting. Checks will be performed by automated tools and give you a success message if the changes are expected to past all lint checks.

### Continuous Integration

When opening a PR from a fork, some of the CI checks must be manually triggered by a member of the team. That means you don't need to worry if some of the CI checks are not running—we'll take care of it when we review the PR and, if there are any issues, we'll let you know.

### PR merge policy

* PRs require one reviewer to approve the PR before it can be merged to the base branch
* We keep the PR git history when merging (merge via "merge commit")
* The reviewer who approved the PR may merge it right after approval (without waiting for the PR author) if all checks are green. 
* The reviewer may also suggest, make changes, or decline the PR for various reasons. Know that we really appreciate and value the input and contribution effort. Start a discussion in issue tickets, PRs, or under [discussions](https://github.com/gyund/fundamental-analysis/discussions) to help plan your efforts effectively.
