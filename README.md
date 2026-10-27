# CSC418 Lab Midterm: Assignment Submission Portal

## What the question requires

1. A portal accepting name, registration number, assignment title and submission URL. Validate, save and list submissions. No file upload is required.
2. GitHub repository with app, tests, CI workflow, local receiver and setup instructions.
3. Tests on EVERY push: valid submission saved/listed; missing registration rejected; invalid URL rejected/not saved.
4. Actual test results automatically POSTed to a local HTTP receiver and saved as `test-report.json`, for successful AND failing test runs.
5. Demonstrate three pushes: passing, deliberately broken, then corrected. Capture pipeline and local JSON evidence for all three.

Marks: portal 8 + GitHub 4 + tests 10 + local report 14 + demonstration 4 = 40 core marks. The paper separately mentions viva: 15. Optional Pages 5 + email 5 bonus marks.

## Chosen solution

Python 3.10+ standard library only. No pip packages, Flask or Docker needed. SQLite persists submissions. Three unittest tests make real HTTP requests against a fresh temporary database. A Windows self-hosted GitHub Actions runner checks out the pushed commit, executes tests and POSTs the resulting JSON to the receiver on the same PC.

Flow: Git push -> GitHub Actions -> your Windows runner -> real HTTP tests -> POST localhost:8765/report -> receiver saves test-report.json. Test failures still deliver the report, then exit with code 1 so the test stage is red.

IMPORTANT: Report delivery is not a manual download. `ci-report.json` is the sender's generated file; `test-report.json` is independently written by the HTTP receiver. Receiver history preserves all three demonstrations automatically.

## 80-minute plan

| Minutes | Work |
|---|---|
| 0-10 | Extract this folder, check Python/Git, start portal, submit valid and invalid data. |
| 10-20 | Run tests; start receiver in a separate terminal; run a local report-delivery check. |
| 20-35 | Create GitHub repository, register Windows self-hosted runner, start it. |
| 35-45 | Push working project; capture green pipeline and passing local JSON. |
| 45-55 | Introduce the one-line defect, push, capture red pipeline and failing local JSON. |
| 55-65 | Restore the line, push, capture corrected green pipeline and JSON. |
| 65-75 | Check screenshots, README and repository URL; prepare viva answers. |
| 75-80 | Submit and retain buffer. Only attempt bonuses after the core workflow works. |

## 1. Open the project on Windows

Extract the ZIP to `D:\CSC418_Lab_Midterm`, so `portal.py`, `README.md` and `.github` are directly inside that folder. In VS Code choose File > Open Folder, select it, then Terminal > New Terminal. Commands below use PowerShell.

```powershell
cd D:\CSC418_Lab_Midterm
python --version
git --version
python portal.py
```

Use real Python 3.10 or newer. If Windows opens Microsoft Store or says Python is missing, install Python with PATH enabled, restart VS Code and check again. If `py --version` works but `python` does not, fix Python's PATH before starting the runner; the workflow uses `python`.

Open `http://127.0.0.1:5000` in your browser. Submit your name, registration number, title and a valid `https://...` link. The saved submission appears on the right and remains after restart in `submissions.db`. Try a blank registration and an invalid URL too. Validation runs on the backend, even if browser validation is bypassed.

Keep this terminal open if you want the app visible during your demonstration.

## 2. Start receiver and check local tests

Open a SECOND terminal in the project folder:

```powershell
python receiver.py
```

Leave it running. Reports will be saved in this original project folder, not in the runner checkout. For a different location, use `python receiver.py --output-dir D:\CSC418-Reports`.

Open a THIRD terminal:

```powershell
python run_tests.py
python run_tests.py --send
Get-Content .\test-report.json
```

Expected: 3 passed, 0 failed. The receiver terminal prints a saved-file confirmation. Local runs use local Git metadata or `local`; real GitHub runs automatically populate repository, branch, full commit SHA, pipeline run ID, attempt and UTC execution timestamp.

## 3. Create repository and register the runner

In GitHub, create an empty repository called `csc418-lab-midterm`. Use a private repository for this self-hosted demonstration if your submission rules allow it, and give your instructor access. If a public repository is required, keep the workflow push-only and restrict write access to trusted people. Do not add a README, license or .gitignore on GitHub because these are already in this folder.

On your new repository go to Settings > Actions > Runners > New self-hosted runner. Select Windows and x64. GitHub displays the current exact download and registration commands. Run those commands in a NEW PowerShell window, using a separate directory such as `C:\actions-runner`.

Use GitHub's generated URL/token, not placeholders from someone else's instructions. Accept the default runner labels. For this short lab, answer `N` if asked to install as a service. Start it with:

```powershell
.\run.cmd
```

Leave the runner window open. It should say `Listening for Jobs`, and GitHub should show it as online/idle. Your receiver must run on this SAME Windows computer. No tunnel or forwarding client is needed because the CI runner itself is local.

Before registration, ensure Python and Git work in the runner's PowerShell window too. Runner installation needs internet and can take several minutes.

## 4. Push the working project (PASS)

In the THIRD terminal, inside `D:\CSC418_Lab_Midterm`:

```powershell
git init
git branch -M main
git add .
git commit -m "Add portal, automated tests and local report delivery"
git remote add origin https://github.com/YOUR_USERNAME/csc418-lab-midterm.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Sign in when prompted. If Git requests identity, set `git config user.name "Your Name"` and `git config user.email "your-email@example.com"`, then retry the commit. If `origin` already exists, use `git remote set-url origin ...` instead of adding it again.

Open repository > Actions > Portal CI and local report. Wait for the test job to finish. The runner checks out the pushed revision automatically; you do not manually copy files into the runner directory.

Expected: green test job, three passing tests. In your original project terminal:

```powershell
Get-Content .\test-report.json
```

Verify the new report contains the GitHub repository, the pushed commit SHA, run ID, 3 passed, 0 failed and `overall_status: passed`. Take the pipeline screenshot and local JSON screenshot BEFORE your next push.

## 5. Introduce a real defect (FAIL)

In `portal.py` change ONLY the `REQUIRED_FIELDS` line from:

```python
REQUIRED_FIELDS = ("name", "registration_number", "assignment_title", "submission_url")
```

to:

```python
REQUIRED_FIELDS = ("name", "assignment_title", "submission_url")
```

This removes registration validation. A submission without a registration number is now saved incorrectly. Leave the tests unchanged; the missing-registration test must discover the defect.

```powershell
git add portal.py
git commit -m "Demonstrate defect: missing registration validation"
git push
```

Wait for this run to complete before continuing. Expected: red test job, 2 passed, 1 failed. The failure contains `201 != 400`. The report is STILL delivered because `run_tests.py` sends it before returning the failure exit code.

```powershell
Get-Content .\test-report.json
```

Capture the red job, failed assertion, and local JSON showing the new commit, `failed: 1`, test failure message and `overall_status: failed`. This is a genuine executed failing test, not a hardcoded report.

## 6. Fix the defect (PASS again)

Restore the original `REQUIRED_FIELDS` line including `"registration_number"`:

```powershell
git add portal.py
git commit -m "Fix registration validation"
git push
```

Wait for green CI and check `test-report.json` again. Expected: 3 passed, 0 failed, new commit SHA. Capture both screenshots. The `report-history` folder automatically retains all received reports, including the failing one. Finish with the fixed source committed.

## 7. Evidence and submission

- GitHub repository URL and README setup instructions.
- Portal screenshot with all four fields and a saved submission.
- First passing Actions run and corresponding local JSON.
- Failing Actions run/assertion and corresponding local JSON.
- Corrected passing Actions run and corresponding local JSON.
- Receiver terminal confirmation; show report history if asked.
- Keep portal, receiver and runner windows open during the demonstration.
- Include Pages URL and received emails ONLY if you actually complete those bonuses.

Do not submit the pre-exam local verification as proof of GitHub CI. Your evidence must show your actual three pushed commits and their reports. No personal name is hardcoded in the portal; enter the correct name yourself.

## Optional bonus: conditional GitHub Pages (+5)

The folder `docs` contains a static demo with browser-local storage. It explicitly labels itself as a demo; GitHub Pages cannot run the Python/SQLite backend.

1. First confirm Pages is available for your repository/account. Availability for private repositories depends on your plan and organization policy. Do not change repository visibility merely to enable a bonus without considering your runner access.
2. Repository Settings > Pages > Build and deployment > Source: GitHub Actions.
3. Settings > Secrets and variables > Actions > Variables > New repository variable. Name `ENABLE_PAGES`, value `true`.
4. Make a small README change and push to main. The `deploy` job needs the successful `test` job and therefore runs only after all tests pass for that push. On a failing run it is skipped; the previous deployment remains published.
5. Copy the actual URL from the deploy job or Pages settings; usually `https://YOUR_USERNAME.github.io/csc418-lab-midterm/`.
6. For bonus evidence, demonstrate a successful deployment, a later failing push that skips deployment and leaves the old site available, then the corrected passing push.

The deployment checks out the same workflow revision as the tests. No pull_request trigger is configured for this local runner.

## Optional bonus: email report (+5)

`send_email.py` sends actual results inline AND attaches JSON using SMTP STARTTLS. Use an email account/provider that already supports SMTP credentials. Setting up a new SMTP account is outside the core 80-minute plan.

Set these repository Actions SECRETS (never commit passwords):

| Secret | Value |
|---|---|
| SMTP_HOST | Your SMTP server hostname |
| SMTP_PORT | STARTTLS port, normally 587 |
| SMTP_USER | Authorized sender/login address |
| SMTP_PASSWORD | Provider-issued SMTP password or app password |
| REPORT_TO | Address that should receive test reports |

Set Actions VARIABLE `ENABLE_EMAIL` to `true`. The workflow's email step uses `always()` so it executes after both successful and failed tests, provided a report was generated. A checkout/interpreter failure is not a completed test run and cannot create test results. Capture received passing and failing emails with commit SHA and test counts.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Actions remains queued | Start `C:\actions-runner\run.cmd`; check online status and Windows/X64 labels. |
| Connection refused on port 8765 | Start `python receiver.py` on the same PC as the runner. |
| Receiver running but JSON not visible | Look in its printed output directory; the default is the terminal's working directory. |
| Test assertions pass but CI is red | Read delivery errors. Delivery failure correctly fails the job too; the report requirement is mandatory. |
| Local JSON has old commit | Wait for the run; check receiver logs and make sure it was started before the push. |
| Port already in use | Stop the old receiver/portal with Ctrl+C; use a single receiver on 8765. |
| Page shows old source after editing | Restart `python portal.py`; tests create their own fresh server each run. |
| GitHub workflow missing | Confirm `.github/workflows/ci.yml` was extracted and committed. |
| Python missing in Actions | Make Python accessible on PATH for the runner account, then restart its window. |
| Pages job skipped | Expected when disabled, on non-main branches, or after test failure. |

## Viva: short answers

- CI means code changes are tested automatically on each push.
- GitHub Actions reads `.github/workflows/ci.yml`; `on: push` triggers the pipeline.
- A self-hosted runner executes GitHub jobs on my own computer.
- Localhost always means the machine running that process. A GitHub-hosted runner's localhost is not my laptop; my runner is on my laptop.
- The receiver listens for an HTTP POST and writes the received JSON to disk automatically.
- SQLite saves application submissions. JSON stores test execution results. They serve different purposes.
- A valid submission test checks both saving and listing, not only a success message.
- The negative tests verify rejection AND no saved record.
- Tests use separate temporary databases, so test data does not change real submissions.
- A failed test produces a nonzero exit code. Delivery happens before that exit, preserving the failing report.
- The report uses GitHub-provided repository, branch, commit SHA and run identifier, so it identifies the tested revision.
- GitHub Pages hosts the static demo; `needs: test` prevents deployment after a failed test job.
- Email credentials are read from CI secrets, not written in code.

## Verification scope

This package can be verified locally for pass/fail/fix and automatic HTTP report delivery. GitHub registration, real pushes, Pages publication and real email delivery must be completed in your account. Do not claim deployment or emails until you see them succeed.

Reference: https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
