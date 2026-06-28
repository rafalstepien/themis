# Explanation of start_sha, head_sha and base_sha

```
main:    A ── B ── C          ← start_sha (tip of main when MR was opened)
                  \
feature:           C ── D ── E  ← head_sha (tip of your feature branch)
```

---

```
main:    A ── B ── C ── F     ← start_sha would update, but base_sha stays C
                  \
feature:           C ── D ── E  ← head_sha
```