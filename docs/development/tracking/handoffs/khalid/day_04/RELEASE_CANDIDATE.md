# Two-exit desktop candidate

2026-11-20, Khalid. Suhita's remaining implementation was accepted in [PR #9](https://github.com/khalid999devs/Echo_Heist/pull/9). [PR #10](https://github.com/khalid999devs/Echo_Heist/pull/10) merged the two-exit map, pursuit and final report changes. The Core security revision adds a fifth guard, wider cones, solid chassis clearance and consistent stun audio. See current Status for the build and test baseline.

- [Verification and package identities](../../../../quality/reports/release_candidate/CORE_SECURITY.md)
- [Current phase gates](../../../STATUS.md)
- [Player guide](../../../../release/draft/PLAYER_GUIDE.md)
- [Earlier physical Windows QA](../../../../quality/reports/phase08/suhita/WINDOWS_QA.md)

```sh
git switch main
git pull --ff-only
uv sync --locked --all-extras
uv run --locked echo-heist --data-dir .local/qa-candidate
```

On seed 1042, use either stairway, steal the Core and check both exit markers with Tab. Use the Entry Airlock after the Security return or the Cargo Airlock via the Research return. C crouches, E interacts, and Shift gives the timed burst. Use Q for Echo, F for EMP and Space for stun. A stunned guard still blocks the center of its lane. On the Core floor, check that amber cones are readable, pursuit turns red, an impact plays once and nearby guards move toward the clang. A guard can inspect a hiding spot it saw you enter.

For Companion, open the Workshop, choose Balanced and deploy seed 1042 with baseline NEXUS memory. F2 shows the decision panel. D opens the actual report and its saved decision notes. Report on the title screen opens persistent history after a relaunch. The native comparison, video and captures are local under `output/release-candidate/`.

Windows P08-SR1 still needs an exact-candidate physical Human win and capture/retry check, both exits, prop/audio and accessibility review, and real player times for the pace calibration. Follow the older PowerShell setup using current `main` and a fresh QA data directory. If the CI artifact cannot be downloaded, run `uv run --locked --all-extras python scripts/packaging/build.py` on Windows and use the resulting ZIP. Keep Windows and Mac evidence separate. Itch.io, source licensing/visibility and final academic submission are later release gates.
