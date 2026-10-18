# V1 desktop release plan

Authority: PDF p. 19 and explicit user priorities. Status: no builds, hosted repository, itch.io page or publishing credentials have been verified.

Active schedule: complete playable initial draft after P08 within four development days. Khalid owns all P01 setup/first native smoke work and P08 build/manifests; Suhita owns P08 gameplay UX QA, comparison report and demonstration materials, with both checking the combined result. Public release can happen on Day 4 if all gates pass; these eight phases do not imply unperformed QA has passed.

## Target matrix

| Target | V1 priority | Build requirement | Launch gate |
| --- | --- | --- | --- |
| Windows x64 | Primary | Windows x64 runner/Python; PyInstaller one-folder executable archive | Both modes and clean-machine QA pass |
| macOS Apple Silicon (arm64) | Primary | macOS runner, arm64-compatible Python and dependencies; `.app` bundle archive | Native Apple Silicon and real download/open QA pass |
| Linux x64 | Optional | Native Linux x64 build with documented distro/glibc baseline | Include only after its independent clean-machine tests pass |
| Browser | Future | Outside V1 | No V1 implementation or advertising |
| Steam | Future possibility | Outside V1 | No V1 integration or store promise |

The minimum Windows/macOS versions, hardware baseline, runner availability and signing setup are open release decisions. Determine candidates through P01/P02 toolchain compatibility and native checks, then publish only actually supported versions. Do not claim all macOS hardware, Intel Mac support or all Linux distributions from one build.

## Native packaging policy

Use PyInstaller one-folder packaging, with a Windows windowed executable or native macOS `.app`. Preserve complete folder contents in each ZIP. The [official manual](https://pyinstaller.org/en/stable/index.html) states PyInstaller is not a cross-compiler, so each OS needs its own build job. The [macOS feature notes](https://pyinstaller.org/en/stable/feature-notes.html) describe architecture and signing requirements; verify the arm64 slices of Python, bundled libraries and the resulting app instead of relying on the host label.

Package resources explicitly and read them independently of working directory. Saves/logs/profiles use writable application data. Include player instructions, controls, version, credits/license notices and known issues. Exclude test caches, local profiles, large diagnostics, design PDFs, credentials and source-environment folders. The public source is distributed through GitHub separately.

Build from a clean release commit and locked environment. Produce names such as `echo-heist-1.0.0-windows-x64.zip` and `echo-heist-1.0.0-macos-arm64.zip`; use prerelease versions while testing. The release manifest records commit, Python/tool versions, dependency-lock/map/config hashes, OS/architecture, archive SHA-256, actual signing/notarization status and linked QA reports. Never call an ad-hoc-signed app Developer-ID signed/notarized.

## Day 1 packaging smoke test

Build the small working app on each primary OS. Launch outside the repository on a machine without the development environment, render a packaged resource, save settings, close and reopen, and test audio-disabled behavior. This proves packaging basics, not final gameplay quality. Record unavailable native runners as blockers immediately.

Complete the available native smoke build on Day 1 and confirm access to the other primary runner that day. By Day 4, rebuild both draft archives from the same candidate, record hashes/signing state and actual native test results, and supply setup/controls/known issues plus a short gameplay demonstration. Label archives as prerelease drafts until the full release matrix passes. Linux work is outside the required four-day sprint and must not displace either primary platform.

## Final clean-machine matrix

Run against the downloaded release archives, not just CI build directories.

| Check | Windows x64 | macOS arm64 | Optional Linux x64 |
| --- | --- | --- | --- |
| Artifact architecture and contents verified | NOT_RUN | NOT_RUN | NOT_RUN |
| Extract/install and launch without Python | NOT_RUN | NOT_RUN | NOT_RUN |
| OS download/security flow tested and accurately documented | NOT_RUN | NOT_RUN | NOT_RUN |
| Both modes immediately selectable | NOT_RUN | NOT_RUN | NOT_RUN |
| Complete core/lockdown/extraction and capture/retry | NOT_RUN | NOT_RUN | NOT_RUN |
| Workshop profile save, same/new seed, memory reset | NOT_RUN | NOT_RUN | NOT_RUN |
| Settings/history/logs survive relaunch in writable paths | NOT_RUN | NOT_RUN | NOT_RUN |
| Controls, pause, focus, fullscreen, scaling and subtitles | NOT_RUN | NOT_RUN | NOT_RUN |
| Missing audio device, mute and volume behavior | NOT_RUN | NOT_RUN | NOT_RUN |
| Performance and no-path/stall regression checks | NOT_RUN | NOT_RUN | NOT_RUN |
| Credits, troubleshooting, uninstall/save instructions | NOT_RUN | NOT_RUN | NOT_RUN |

Link reports from each cell when executed, including OS version, machine and artifact hash. CI smoke tests supplement human hardware QA. A passing macOS run cannot fill the Windows column.

For macOS, test the exact downloaded ZIP including its quarantine/Gatekeeper behavior and preserved app permissions/symlinks. Prefer Developer ID signing/notarization if available; otherwise document the actual unsigned/ad-hoc status and the OS-supported per-app opening process validated on supported macOS. Do not recommend globally disabling security controls. Record any Windows security prompts accurately too.

## Public GitHub readiness

- Source matches the release tag and lock; no private keys or local user data are present.
- README gives pitch, screenshots, controls, supported targets, install/source-run/test/build instructions and troubleshooting.
- Source license is selected by its owner; asset/dependency notices and credits are included.
- Algorithm documentation links to actual modules and reproducible experiments.
- Issues/known limitations, exact version, downloadable release artifacts if used, and video link are accurate.
- Public visibility and unauthenticated source/video access are verified before academic submission.

Public source and free binaries do not by themselves define a software license. Finish that decision before release. Preserve the idea PDF as the design authority; separately review its public redistribution status when preparing the public repository.

## itch.io page and publication

Create a **downloadable** game project with separate Windows x64 and macOS arm64 archives and correct platform tags. itch.io's [creator guide](https://itch.io/docs/creators/getting-started) describes the usual platform-per-ZIP approach. Set it free with no payment required; do not attach required files to paid tiers. Confirm the chosen donation setting still permits free downloads.

Prepare the page privately/draft first: short sci-fi stealth pitch, both modes, truthful AI/Workshop description, representative images/video, controls, supported architecture/OS, installation steps, credits and known issues. Do not advertise Linux until tested, or browser/Steam as available. Verify filenames and hashes after upload.

Actual remote repository creation, visibility changes, itch.io uploads/publication and academic submission are future execution steps requiring the correct account/project context. This planning pass does not perform them. Prepare the candidate and evidence before asking for any missing release decision.

## Submission and maintenance

Submit the working public GitHub link and gameplay demonstration video; attach experiment/algorithm evidence when the rubric allows it. Verify links in an unauthenticated session and record submitted version/commit/date.

After launch, triage crash/startup/save/mission-blocking bugs first. Preserve the released logs/schema compatibility, reproduce against the exact version, fix with focused regression coverage, rebuild and retest both primary archives, then issue a versioned patch and changelog. Retain the previous known-good archives so a faulty upload can be rolled back.
