# AGENTS.md

Static Church of God map. GitHub Pages serves the repo root from `main`: https://78tacos.github.io/cog-locations/

- Test: `python3 -m unittest discover -s tests -v`. CI runs the same discover as `python -m unittest discover -s tests -v`. It must pass before you open a PR.
- Data changes follow `.cursor/skills/cog-batch/SKILL.md`. Read it first.
- `churches.json` and `churches.js` are written together by `scripts/refresh.py` (`write_outputs`). Never hand-edit either one.
- A refresh must pass every published state (the list in `.github/workflows/refresh.yml`). A shorter list deletes states.
- States you didn't target must stay identical to the base commit. Put the base SHA and the expected total in the PR body.
- UI-only changes (`index.html`, `directory.html`) don't touch the data files. Update the string assertions in `tests/test_southeast.py` to match.
- `MIN_STATEWIDE` (100) and `MIN_PER_STATE` (15) are in `scripts/refresh.py`. Change them only when the task says to.
- Open one PR per task and keep the diff to what the task asks for.
