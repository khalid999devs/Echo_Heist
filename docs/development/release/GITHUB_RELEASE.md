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
