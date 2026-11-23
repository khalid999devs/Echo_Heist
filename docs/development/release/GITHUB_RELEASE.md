# GitHub release record

Owner Khalid. Recorded 2026-11-23, Asia/Dhaka.

## What was published

Release [ECHO HEIST 0.1.0a1](https://github.com/khalid999devs/Echo_Heist/releases/tag/v0.1.0a1) sits on the annotated tag `v0.1.0a1`, which points at commit `bbc2e0cd3a4275dcabf41c27b52afe064b727377`. The version is the alpha `0.1.0a1` from `src/echo_heist/__init__.py`. The release notes cover the downloads, first-launch steps, what the build contains, known limits and the license.

| Asset | Bytes | SHA-256 |
| --- | --- | --- |
| `echo-heist-0.1.0a1-windows-x64.zip` | 112,640,838 | `449d8a7300ead9e73017c8acb1a3ef61308b2895d6ca4e7ee5ee449cfa4ffbda` |
| `echo-heist-0.1.0a1-macos-arm64.zip` | 113,465,889 | `9063f4ea05fd70b7d7090fb3f28703de714b45f58e2561ee0b68ce6513391e98` |

After the upload, GitHub reported the same SHA-256 digests for both assets. The README links to both files directly, and both links returned HTTP 200 on 2026-11-23.

## How the zips were built

Both zips come from the manual run [45198177450](https://github.com/khalid999devs/Echo_Heist/actions/runs/45198177450) of `.github/workflows/checks.yml`, started on branch `docs/public-readme` at `bbc2e0c`. All three jobs passed. They are headless-checks, windows-x64 on `windows-2022` and macos-arm64 on `macos-15`.

Each manifest records source commit `bbc2e0c`, a clean working tree, Python 3.13.17, PyInstaller 6.22.3, fingerprint schema 17 and gameplay hash `726a959e79e91538633c3abbc6a6e96daa08bbd25c3d014d4d37bbd710f04b72`. Signing is `unsigned` for Windows and `ad-hoc; not notarized` for macOS.

Commands used after the run finished.

```sh
gh run download 45198177450 -R khalid999devs/Echo_Heist -D <scratch>/release/v1
git tag -a v0.1.0a1 bbc2e0c -m "ECHO HEIST 0.1.0a1"
git push origin v0.1.0a1
gh release create v0.1.0a1 -R khalid999devs/Echo_Heist --verify-tag \
  --title "ECHO HEIST 0.1.0a1" --notes-file notes.md --latest \
  echo-heist-0.1.0a1-windows-x64.zip echo-heist-0.1.0a1-macos-arm64.zip
```

## Checks on the downloaded zips

- Both CI smoke summaries report `passed: true` with scope `CI dummy video`. The frozen app started in desktop and headless modes, loaded its resources, rendered frames, saved settings and reproduced the same state and event hashes.
- `shasum -a 256` of each downloaded zip matches the hash in its manifest.
- `unzip -l` shows `LICENSE.md` at the root of each zip, next to `EchoHeist/` on Windows and `Echo Heist.app` on macOS.
- On Khalid's Apple Silicon Mac, the macOS zip extracted with `ditto -x -k` passes `codesign --verify --deep --strict`, and the extracted app prints `0.1.0a1` for `--version`.

## Not tested yet

- Downloading and playing these exact zips by hand on clean Windows and macOS machines, including the SmartScreen and Gatekeeper first-launch steps.
- Developer ID signing, notarization and Windows code signing.
- Intel Mac and Linux builds. Those platforms can only run the game from source.

The clean-machine matrix in the [release plan](RELEASE_PLAN.md) stays NOT_RUN.

## License

On 2026-11-23 Khalid chose the PolyForm Strict License 1.0.0 for the source and the project's own assets. The root `LICENSE.md` names both authors, explains what needs written permission, lists third-party material (Oxanium fonts under the SIL Open Font License, CC0 audio and the locked dependencies) and then gives the license text unchanged.

`pyproject.toml` declares `LicenseRef-PolyForm-Strict-1.0.0` with `license-files`, because PolyForm Strict has no SPDX identifier. `uv build` writes `License-Expression: LicenseRef-PolyForm-Strict-1.0.0`. `scripts/packaging/build.py` now adds `LICENSE.md` to the root of every release zip, outside the signed macOS bundle.

## README and repository page

The README was rewritten for the public repository. It has a banner, four gameplay clips stored as animated WebP in `docs/media/`, download links, controls, the AI roster, engineering notes and the license terms. The repository description and twenty topics were set with `gh repo edit`. A 1280 by 640 social preview image was prepared, and it has to be uploaded by hand in the repository settings.

## Commit history rewrite

On 2026-11-23, at Khalid's request, six commit messages were rewritten to remove co-author trailer lines. The file trees did not change. `main` and `docs/public-readme` were force-pushed with a lease.

| Old | New | Branch |
| --- | --- | --- |
| `59c5272` | `1f439eb` | main |
| `90193b0` | `b908be7` | main |
| `4483936` | `4b9f646` | main |
| `6aa8f82` | `f703e4d` | main, PR #12 merge |
| `90c4382` | `e565de2` | docs/public-readme |
| `332d5a0` | `bbc2e0c` | docs/public-readme |

Every other clone, including Suhita's, needs to re-sync once. Save any unpushed work on its own branch first, then run the following.

```sh
git fetch origin
git switch main
git reset --hard origin/main
```

[PR #13](https://github.com/khalid999devs/Echo_Heist/pull/13) carries these changes. It is merged with a merge commit rather than a squash, so the tagged commit stays in the history of `main`.

## Release 0.1.0a2

Published on 2026-11-24 as [ECHO HEIST 0.1.0a2](https://github.com/khalid999devs/Echo_Heist/releases/tag/v0.1.0a2), the latest release. The annotated tag `v0.1.0a2` points at `e9d60cbe6a4a03e51a94a9a202d53bbf12839204`, the merge of [PR #14](https://github.com/khalid999devs/Echo_Heist/pull/14). It ships the [Core room balance](../planning/balance/CORE_ROOM.md). The description lists the improved logic only and points to the 0.1.0a1 install steps. v0.1.0a1 stays published as the presentation build.

| Asset | Bytes | SHA-256 |
| --- | --- | --- |
| `echo-heist-0.1.0a2-windows-x64.zip` | 112,643,990 | `2138b544ba6022b5838edbd4c203493608a47336c99a74a100d86257eb3dbc09` |
| `echo-heist-0.1.0a2-macos-arm64.zip` | 113,468,257 | `6cdec491a37c77458b5d289b8c35043655143d668f24b39081b9140320e526e5` |

Both zips come from the main push run [45244029746](https://github.com/khalid999devs/Echo_Heist/actions/runs/45244029746) on the merge commit, where headless-checks, windows-x64 and macos-arm64 passed. The PR run [45241705134](https://github.com/khalid999devs/Echo_Heist/actions/runs/45241705134) on the branch head passed as well, and the merge commit has the same file tree. Each manifest records version 0.1.0a2, a clean working tree, Python 3.13.17, PyInstaller 6.22.3, fingerprint schema 17 and gameplay hash `34e81693bd86de8b25d0dde651d03608bb2cb43d3ec8e894a7ed13d53418c159`. Signing is unchanged, `unsigned` for Windows and `ad-hoc; not notarized` for macOS.

Checks on the downloaded zips. Both CI smoke summaries report `passed: true` with scope `CI dummy video`. Each SHA-256 matches its manifest, and each zip carries `LICENSE.md` at its root. On Khalid's Apple Silicon Mac the extracted app passes `codesign --verify --deep --strict` and prints `0.1.0a2` for `--version`. Hands-on play of these exact zips on clean Windows and macOS machines has not been done yet.

The README download links now point to the 0.1.0a2 zips, and its wide-test sentence uses the new sweep numbers.
