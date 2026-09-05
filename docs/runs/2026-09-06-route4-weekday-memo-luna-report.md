Implemented ROUTE-4.

Design:
- `workplace_team`: closure-local weekday memo of `EdgeColumns`, bounded to 5 entries.
- `workplace_transient`: closure-local weekday memo of per-workplace physical-agent lists, bounded to 5 entries.
- Daily transient participant draws and ring construction remain unchanged.
- `RouteSnapshot` shares cached column arrays without copying.

Base SHA: `bff0eb4fbae1174df044bd2b1e361841b1ae8a8a`

Verification:

- 180-date parent equivalence: `1 passed`
- Dynamic routes: `6 passed`
- Focused regression suite: `71 passed`
- Full suite: `314 passed, 5 warnings`
- Ruff, format, lock check, compileall, and 15-module mypy: passed
- Relocation check: passed
- `git diff --check`: passed

Full benchmark comparison:

```text
fingerprints identical
standard bus: A_wall/B_wall=0.807419
standard care_resident: A_wall/B_wall=1.012046
standard care_staff: A_wall/B_wall=0.919057
standard community_indoor: A_wall/B_wall=1.016855
standard community_outdoor: A_wall/B_wall=1.010603
standard household: A_wall/B_wall=1.048703
standard school_class: A_wall/B_wall=0.962913
standard school_cross_class: A_wall/B_wall=1.023057
standard shared_vehicle: A_wall/B_wall=1.003427
standard workplace_team: A_wall/B_wall=5.708808
standard workplace_transient: A_wall/B_wall=1.203723
standard total: A_wall/B_wall=1.221935
term-boundary bus: A_wall/B_wall=1.041704
term-boundary care_resident: A_wall/B_wall=1.086482
term-boundary care_staff: A_wall/B_wall=0.878135
term-boundary community_indoor: A_wall/B_wall=0.993721
term-boundary community_outdoor: A_wall/B_wall=0.996626
term-boundary household: A_wall/B_wall=1.048618
term-boundary school_class: A_wall/B_wall=0.970060
term-boundary school_cross_class: A_wall/B_wall=1.005839
term-boundary shared_vehicle: A_wall/B_wall=1.006347
term-boundary workplace_team: A_wall/B_wall=8033.023878
term-boundary workplace_transient: A_wall/B_wall=1.241555
term-boundary total: A_wall/B_wall=1.280479
```

Absolute workplace timings:

```text
standard workplace_team: base=6.383820801s branch=1.118240499s
standard workplace_transient: base=9.107442501s branch=7.566064577s
term-boundary workplace_team: base=4.378801299s branch=0.000545100s
term-boundary workplace_transient: base=6.263481396s branch=5.044869902s
```

Full seed-101 hashes matched:

```text
M4/network: 49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
latent logical hash: 2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c
latent outcome hash: f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac
```

Changed files only:

```text
 M  src/jersey_outbreak/network_generator.py
?? tests/test_route4_weekday_memo.py
```

No commit made.