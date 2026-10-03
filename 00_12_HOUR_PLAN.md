# 12-Hour Build Plan

Commit to GitHub at the end of every block (rule 5.3 needs step-by-step history).

| Hours | Block | Output |
|---|---|---|
| 0:00-0:45 | Setup | Repo, folders, FastAPI skeleton, SQLite, .env.example, first commit |
| 0:45-2:15 | Data | Synthetic generator, seed script, 5k transfers with injected patterns |
| 2:15-4:00 | Risk model | Isolation Forest + rules + score endpoint + reason codes |
| 4:00-5:00 | Send-plan | Rate trend forecaster + goal split + fee rules |
| 5:00-6:30 | API | All endpoints wired, Swagger working |
| 6:30-8:30 | Frontend | 3 screens: Sender, Receiver (+Agent panel), Analyst |
| 8:30-9:15 | LLM explainer | Grounded explanations with template fallback |
| 9:15-10:15 | Deploy | Live URL, smoke test from another device |
| 10:15-11:15 | README + report | Full README (rulebook section 6), project report |
| 11:15-12:00 | Video + buffer | 3-minute demo video, final push |

Cut order if late: agent forecast, then voice, then fairness chart.
Never cut: sender flow, risk review queue, README, video.

Rule 9.3: do not write challenge-specific code before the official problem is published.
