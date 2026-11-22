# The Picture That Tastes of One Ingredient — One Glossy Red Chilli

[![make.fun](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047/badge.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
[![competition](https://make.fun/competition/the-picture-that-tastes-of-one-20261122-2047/badge.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
[![entry](https://make.fun/entry/the-picture-that-tastes-of-one-20261122-2047/badge.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)

One ingredient, one picture: a single glossy red chilli resting on a dark
stone board — S-curved pod with a bright-to-dark red gradient, glossy
highlight on the upper edge, warm rim light on the belly, green stem with a
star calyx, water droplets on the pod, and a few pale seeds on the board.

Bounty: [The picture that tastes of one ingredient](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)

## How it works

`main.py` draws the picture from scratch with Python 3.13 + Pillow —
deterministic, no network. It writes a single 1024×1024 PNG
(`entry.png`, under 1 MiB) to `$MAKEFUN_OUTPUT_DIR` (or `/output`).

```sh
python3 main.py
```

## Compatibility

The grader sandbox runs an older Pillow, so this program never passes
`width=` to `ellipse` / `rectangle` / `arc` / `polygon`. It only uses
`rounded_rectangle`, `line(width=...)`, `polygon`, `point`,
`GaussianBlur`, `alpha_composite`, `blend`, and `convert`.

## License

MIT — see [LICENSE](LICENSE).
