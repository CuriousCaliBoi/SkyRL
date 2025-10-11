## Intent
- Why now? Why this size?
- Interfaces touched (I/O, invariants)?
- Risks + rollback steps?

## Premortem (5 min)
- [ ] What’s the fastest way this fails?
- [ ] What would make rollback painful?
- [ ] Hidden coupling? Data migrations? Rate limits?
- [ ] Single-point reviewer risk?
- [ ] Kill rule: “We stop if ____ by (date/time).”

## Self-Review Before Requesting Review
- [ ] I ran tests/lints locally; CI green.
- [ ] Subtraction pass done; complexity decreased.
- [ ] Public interfaces documented; edge cases asserted.
- [ ] PR body includes: intent, constraints, SVU, premortem notes, rollback.

## Micro-Closure (end of block)
- [ ] Tests green
- [ ] WIP committed
- [ ] TODOs logged
- [ ] Timebox set for next step

