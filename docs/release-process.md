# Release Process

## How to release new version of themis

### 1. Repository `themis`
1. Create feature branch
2. Implement the feature
3. Create MR to `main`
TODO: Needs automation. Implement CI pipeline here: build image -> run linters -> run tests
4. Collect approvals and merge
5. Call `./scripts/push_image.sh` with target version (not prefixed with v, eg. `0.1.0-dev` is correct while `v0.1.0-dev` is not correct).
TODO: Needs automation. Release should not be manual and this script should be triggered as a part of tag pipeline
6. Verify if the image was pushed to Dockerhub


### 2. Repository `themis-ci`
1. Checkout to branch `feat/bump-to-<version>`, for example `feat/bump-to-0.1.0-dev`
2. Update job `themis-ci/templates/themis-ci.yml` with correct image version (eg. `rafalstepien/themis:0.1.0-dev`)
3. Merge Request -> merge to main
4. Create a tag with name matching the image version (in this example `0.1.0-dev`)

> Remember: Component tag version must always match image version


### 3. Repository `themis-example` (or client repo)
1. Update version of the included component in `.gitlab-ci.yml` (eg. to `component: gitlab.com/rafalstepien/themis-ci/themis-ci@0.1.0-dev`)
2. Test if the review is done correctly????