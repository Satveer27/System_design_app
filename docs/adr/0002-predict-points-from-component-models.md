---
status: accepted
---

# Predict points from component models and FPL's rules

A match predictor estimates each club's goals, results and clean-sheet chances; a stat predictor estimates each player's minutes, goals, assists and saves. A calculator applies FPL's scoring rules to these to produce each player's prediction. The team of the week and the best squad are chosen by an optimiser from the predictions, not by a model. A model predicting points directly is added after launch as a challenger, and whichever has been more accurate recently is shown to users.

## Considered Options

- **One model predicting points directly**: simpler, but cannot explain a prediction or produce top scorers, assists, saves and match results.
- **A separate model per user-facing list** (top scorer, top assister, team of the week): duplicated inputs and inconsistent numbers between lists.

## Consequences

- Predictions are calculated in batch an hour before each deadline, locked and stored; the website only reads them.
- Models are tested walk-forward, only on gameweeks after those they were trained on. The training window is chosen by that test.
- A retrained model replaces the current version only if it scores better; every version is recorded in MLflow and shown publicly.
- Double and blank gameweeks must be handled: a player may have two fixtures or none.
