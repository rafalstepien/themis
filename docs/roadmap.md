## Core Value To Deliver
Getting high-signal, contextual feedback directly inside a GitLab Merge Request without the code leaving user's infrastructure.

## Implementation phases
### (✅ done) Phase 1: The Core Pipeline (`0.1.0`)

### Phase 2: High-Signal & Precision (`1.0.0`)
#### Implementation
- [ ] Implement Tree-sitter to chunk changed files into logical code blocks and provide more context for engine
- [ ] Linter Noise Filtering: write a parser for local configuration files and feed the rules into the LLM system prompt with instruction "if you catch it, ignore it"
- [ ] Post Cohorts and Business Requirements as top-level comments 
#### Testing
- [ ] AST Parser tests (unit). Create a folder with "fixture" code files, and write unit tests that feed these files into the tree-sitter engine and assert that it correctly identifies the exact byte-ofsets and logical blocks
- [ ] Linter filter test (unit). Feed your engine a dummy .eslintrc.json file and a sample string of linter rules. Assert that your system prompt compiler accurately parses it and creates instructions telling the LLM to ignore those stylistic choices.
- [ ] JSON Schema Defense (Unit): Write tests for the function that handles the raw LLM response. Feed it malformed JSON, truncated text, or missing fields, and verify your engine handles the error gracefully without crashing the whole pipeline.


### Phase 3: Refinement and making it better (`1.1.0+`)
#### Implementation
- [ ] Build the tool that crawls historical MRs, analyzes discussions and auto-generates rules.json and architecture.json files in the repo
- [ ] Issues sync: pull description and comments from Jira to create Ticket Requirements Verification Matrix
- [ ] `/dismiss` feedback loop: setup the webhook listener to intercept `/dismiss` comments on GitLab MRs, trigger a lightweight pipeline job, and commit updated exceptons to `rules.json`
- [ ] MR Description Mutation: move the cohorts from comments to MR description
#### Testing
- [ ] Indexer Snapshots (Functional): Run your Async Indexer against your test GitLab repository's history. Instead of manually verifying the output every time, use snapshot testing: compare the newly generated rules.json against a known "good" baseline file. If they match, the indexer works.
- [ ] Webhook Payload Simulation (Integration): You don't need to manually type /dismiss in GitLab to test the learning loop every time. Capture a real webhook JSON payload from GitLab once, save it locally, and write a script to HTTP POST that exact payload directly to your local engine or trigger API to verify it kicks off the rules.json update job

## Measuring adoption
- DockerHub pulls: tracking unique image download trends
- GitLab Component Marketplace Metrics: Monitor how many unique project configurations import CI/CD component wrapper
- Using the engine to revew the engine code
- Track the creation of community-submitted `best-practices/` JSON templates