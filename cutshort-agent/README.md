# Cutshort daily apply helpers

Operational notes for the Rafi Ahmed Cutshort automation (Chrome CDP + Cutshort APIs).

## Runtime

- Chrome with non-default `--user-data-dir` (CDP blocked on default profile path)
- Puppeteer-core against `http://127.0.0.1:9222`
- Prefer APIs for questionnaires; UI Apply now + keyboard typing for application notes

## Key endpoints

- Jobs: `GET /findjobs/q?page=N` (+ `skills=00001` .NET, `00075` C#, `00054` AWS, `00486` Azure, `locations=Hyderabad`)
- Apply: `POST /sendreply/jobsignal`
- Thread reply: `POST /sendreply/jobthread`
- Awaiting list: `GET /conversations-v2/candidate?page=1&user_role=candidate&context={seekerId}&convo_status=awaiting`
- Thread: `GET /loadthread-v2/{threadId}`
- Questionnaire: `POST /update-message/{messageId}` with filled `questions` and `screeningSubmitted: true`

## Hard rules

- One job URL at a time (no batch `location.href`)
- Stop if Candidate login missing (`Candidate login` / redirect to `/?redirect_url=%2Fprofile%2Ffind-jobs`)
- Do not invent applies — require Apply path success / View conversation when possible
