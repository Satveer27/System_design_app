---
status: accepted
---

# Use FPL's unofficial API as the main data source

All current-season data comes from the undocumented endpoints that the FPL website itself uses (`fantasy.premierleague.com/api/`), because it is the only source of FPL prices, points, ownership, injury flags, FPL's own expected points and managers' squads. Past seasons are loaded once from the vaastav/Fantasy-Premier-League dataset, without its `xP` column, which was recorded after matches.

## Considered Options

- **Documented football data services** (API-Football, Sportmonks, football-data.org): supported, but none carry FPL-specific data, and free plans are too limited.
- **Licensed data** (Opta, Sportradar): beyond budget.

## Consequences

- FPL's terms forbid automated access and commercial reuse. The site stays free and non-commercial and credits FPL; no permission was sought.
- The endpoints can change without notice. Every response is stored raw in S3, the daily sync checks the data's shape and alerts on change, and the site shows the last saved data if FPL is unavailable.
- Requests are few: a handful per day, plus two per team import, stored for the gameweek.
