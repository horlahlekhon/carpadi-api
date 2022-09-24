/* eslint-disable quotes */
module.exports = {
    branches: ["master", {name: "beta", prerelease: true}],
    plugins: [
        "@semantic-release/commit-analyzer",
        "@semantic-release/release-notes-generator",
        "@semantic-release/changelog",
        [
            "@semantic-release/exec",
            {
                verifyReleaseCmd:
                    "mkdir -p ./artifacts && echo NEXT_VERSION=${nextRelease.version} >> ./artifacts/.VERSION",
            },
        ],
        [
            "@semantic-release/github",
            {
                assets: "release/*.tgz",
            },
        ],
        "@semantic-release/git",
    ],
    preset: "angular",
};
