# Technical Description of The AI Code Reviewer Solution

## Overview
The project consists of two elements:
1. The AI Code Review Engine: wrapped as GitLab CI/CD Component, gets triggered in CI/CD pipeline. Contacts LLM API, Jira API and GitLab API.
2. Async Indexer: Crawls the company's repo, extracts data from past merge requests and creates a `rules.json` file for each module based on that data and commits them to the repository that will be using AI Code Review Engine. The `rules.json` are then used by AI Code Review Engine

Both of the elements will live in the same repository, compiled into a single Docker image and run as follows:
`ai-review-tool --mode=engine` or `ai-review-tool --mode=indexer`


## The AI Code Review Engine
The code will be open-sourced and hosted on GitHub.
The code will be versioned, built as Docker image and pushed to public repository on DockerHub.

The configuration for the Engine will be written by the developers inside the company and will be hosted in the repository, that will undergo the AI Code Reviews. Additionally there will be GitLab Masked Variables exported. The split is as follows:

### config.json
- ID of a reference branch
- ID of a target branch


### GitLab Masked Variables (secrets)
- LLM API Token
- GitLab API Token
- [Optional] Jira API Token

## The GitLab CI/CD Component
Thin wrapper around the `AI Code Review Engine` image. It's job is to wrap the `AI Code Review Engine` into easily pluggable CI/CD component, fetch the config and masked variables from the company and execute the `AI Code Review Engine` code.

The code for the GitLab CI/CD Component will be hosted on GitLab and will follow the structure required for CI/CD Components.


## The Async Indexer
It has two goals: 

1. Crawl the codebase where AI Code Reviews will be executed and download merge requests and their comments/discussions from the past for each module. Then, for each module create `module-x/rules.json` file that will summarize the most important requirements and commit that file to the repository.
2. Crawl the codebase where AI Code Reviews will be executed and identify the architecture of a module (eg. if it follows hexagonal app design, or DDD). Then summarize the key insights and the mapping for future requirements in `module-x/architecture.json`.

The Async Indexer commits will require `skip-ci` mark.


## Setting up the CI/CD pipeline in the company
1. Developers from the company write `JSON` config and commit it to the repository where AI Code Review will be run.
2. Developers from the company export necessary secrets as GitLab Masked Variables in the repository where AI Code Review will be run.
3. Developers add the step to the Merge Request CI/CD pipeline that includes the `GitLab CI/CD Component` that wraps the `AI Code Review Engine`


## The Flow of Reviewing the Merge Request by AI
1. Developer from the company opens Merge Request
2. CI/CD pipeline in that repo triggers `AI Code Review Engine`
3. `AI Code Review Engine` gets the list of changed files in this Merge Request. Each file is in old and new version.
4. Changes are broken down into logical blocks using AST node chunking (like CAST).
5. Based on the files changed, Engine identifies the module (or array of modules if the MR spans across multiple modules) that are changed in this Merge Request.
6. Contexts are aggregated:
    6.1. `module-x/rules.json` is located for the identified module
    6.2. `module-x/architecture.json` is located for the identified module
    6.3. Based on the changes content, the appropriate technology-specific best practices are located (eg. `best-practices/concurrency.json`)
    6.4. Based on the MR description, the business context is downloaded from the Jira ticket
    6.5. The repository local configurations (`.eslintrc.json`, `pyproject.toml`) are fetched and explicitly provided for the LLM to ignore linter-like comments.
7. LLM is requested using company API key. There is one system prompt that requests the data. As a response we receive 1) cohort aggregation, 2) business requirements matrix, 3) code review comments
8. Engine uses GitLab API to do the following:
    8.1. Post "Cohorts" comment (this is only for MVP, later will be updating the MR description)
    8.2. Post "Business Requirements Matrix" comment
    8.3. Post code review comments


## The learning loop after dismissed comment
1. AI makes the comment
2. The developer dissmisses it (eg. via reaction or adding a `/dismiss` comment) marking it as irrelevant
3. GitLab sends Comment Webhook to GitLab Pipeline Trigger API
4. Pipeline Trigger API spins up CI/CD job
5. CI/CD job updates `rules.json` via GitLab API, the auto-generated commit must include `[skip ci]`
