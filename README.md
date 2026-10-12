# ZX-CENF Transpiler

Research prototypes for population-guided quantum circuit optimization with
the ZX calculus.

This repository investigates a central idea from the ZX-CENF proposal: can
experience collected from a population of ZX diagrams help organize
structures and choose rewrites on previously unseen circuits? The current
code implements the main pieces needed to test that question:

- rewrite-order sensitivity analysis;
- CENF-inspired structural clustering;
- multidimensional circuit-cost values; and
- population-guided rewrite selection with held-out evaluation.

The project is a feasibility study, not yet a complete ZX-CENF transpiler.
In particular, the clustering experiment does not yet construct CENF
meta-variables, and its clusters are not yet used by the learned rewrite
policy. The implemented work shows that the ideas can be translated into a
working experimental pipeline and identifies what a fuller integration must
address.

## What is implemented

### 1. Rewrite-order sensitivity

The first experiment applies valid PyZX simplification passes in different
random orders to the same circuit. It then extracts the terminal circuits and
compares their two-qubit gate count, T-count, and depth.

The experiment also records how original spiders survive or change across
runs. This provides the observations used by the clustering stage and tests
the premise that rewrite order creates a meaningful decision problem.

The main natural dataset contains 60 procedurally generated circuits from four
gate-mixture families: Clifford-heavy, balanced, phase-rich, and
entangling-heavy. Each circuit is evaluated under 30 randomized pass orders.

### 2. CENF-inspired structural clustering

For each circuit, the second experiment represents every original spider by
its survival and local-neighbourhood outcomes across the randomized runs.
Local structures are encoded with Weisfeiler--Leman graph hashes, pairwise
normalized mutual information is calculated, and spiders with similar
outcome patterns are clustered.

This is a structural-analysis prototype. It tests whether coordinated regions
can be recovered from alternative reductions, but it does not implement
Holman's full ENF, CENF meta-variable construction, meta-level rewrites, or
the proposed two-stage CENF search.

### 3. Quantale scoring and population-guided selection

Extractable circuits receive the cost vector

```text
(two-qubit gate count, T-count, depth)
```

The quantale prototype supports componentwise addition, maximum, comparison,
and Pareto-related operations. When the optimizer needs one preferred result,
it compares costs by two-qubit count first, depth second, and T-count third.

The training reducer detects a local *crossroad* when matches from at least two
rewrite-rule types overlap. A radius-one structural hash and the complete set
of available rules identify the decision context. For each competing rule,
the experiment forces one candidate, follows the same deterministic greedy
continuation, extracts the final circuit, and records the resulting cost.

Evidence is combined across circuits. A preference is learned only when every
available rule has at least five valid observations from at least five
distinct training circuits and one rule has a unique best mean result. On a
held-out circuit, the learned policy uses that rule when the context recurs;
otherwise it falls back to the same greedy policy used by the baseline.

The instrumented rules are spider fusion, identity removal, pivot, local
complementation, pivot-gadget simplification, and boundary-pivot
simplification.

## Experimental findings

| Experiment | Main observation |
|---|---|
| Rewrite order | 57 of 60 circuits varied in at least one terminal metric; 56 varied in two-qubit count and depth. Of 1,800 attempted randomized runs, 713 produced extractable terminal circuits. Extraction failures were recorded rather than scored. |
| Structural clustering | The 60 circuits contained 3,030 tracked original spiders, of which 1,954 had informative outcome variation. Median silhouette score was 0.110, indicating that the discovered groups were generally weak or overlapping rather than sharply separated. |
| Population guidance | Across five independent populations there were 200 training and 100 held-out circuits. Training produced 5,735 crossroad-action observations, 5,690 valid terminal observations, 49 fully supported contexts, 39 leading ties, and 10 learned preferences. |
| Held-out use | Nine learned contexts recurred, producing 90 table hits and 79 decisions that differed from greedy on 41 circuits. Coverage was 3.32% of held-out crossroad lookups. |
| Learned vs. greedy | The terminal comparison was 4 wins, 90 ties, and 6 losses. The mechanism transferred decisions across circuits, but it did not establish a consistent optimization improvement over greedy selection. |

The final experiment also includes randomized-table, deliberately wrong-rule,
sampled-order, and PyZX `full_reduce` comparisons. The direct learned-versus-
greedy comparison is the main measure of incremental population-guidance
value because both strategies otherwise use the same reducer.

## Installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/hintsete/ZX-CENF-Transpiler.git
cd ZX-CENF-Transpiler

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"
```

The editable install makes the `zx_cenf` package available to the experiment
scripts. The pinned PyZX version used by the repository is listed in
`requirements.txt`.

## Reproducing the natural-population experiments

Run commands from the repository root. The clustering stage consumes the
outputs of the rewrite-order experiment, so run Tracks 1 and 2 in order.

```bash
# Track 1: 60 circuits x 30 randomized rewrite orders
python experiments/ambiguity/run_track1_natural.py

# Track 2: structural outcome clustering from Track 1 observations
python experiments/cenf/run_mi_clustering_natural.py

# Track 3: one 40/20 train/test population-guidance run
python experiments/quantale/run_natural_population.py
```

Track 1 writes to `data/track1_results/natural/`, Track 2 writes to
`data/track2_results/natural/`, and Track 3 writes to
`data/track3_results/natural/` by default.

To reproduce the five independent Track 3 populations used in the report:

```bash
for seed in 17000 117000 217000 317000 417000; do
  python experiments/quantale/run_natural_population.py \
    --base-seed "$seed" \
    --out-dir "data/track3_results/natural_replication_independent/seed_${seed}"
done

python experiments/quantale/summarize_natural_replications.py \
  data/track3_results/natural_replication_independent
```

The generated result directories are intentionally excluded from version
control where configured in `.gitignore`.

## Controlled checks and small examples

The repository includes smaller experiments for checking individual parts of
the pipeline:

```bash
# Generate three toy QASM circuits, then run Tracks 1 and 2 on them
python data/toy/generate_ambiguity_population.py
python experiments/ambiguity/run_track1.py
python experiments/cenf/run_mi_clustering.py

# Verify that the Phase F mechanism can learn a known planted preference
python experiments/quantale/run_positive_control.py

# Test distinct connected motifs with different preferred rules
python experiments/quantale/run_connected_motifs.py
```

These controlled cases validate the machinery. Conclusions about transfer and
optimization effectiveness should be drawn from held-out natural populations,
not from the planted controls.

## Repository layout

```text
src/zx_cenf/
  ambiguity/    randomized rewrite ordering and spider tracking
  cenf/         outcome encoding, mutual information, and clustering
  ingestion/    QASM loading helpers
  quantale/     cost algebra, crossroads, preference learning, and policies
  rewrite/      small educational rewrite utilities

experiments/
  ambiguity/    Track 1 runners
  cenf/         Track 2 runners
  quantale/     controls, natural populations, and replication summaries

data/toy/       reproducible toy-circuit generators
tests/          algebra, valuation, and Phase F pipeline tests
```

The reusable implementation lives under `src/zx_cenf/`; files under
`experiments/` orchestrate datasets, evaluations, and result output.

## Tests

```bash
pytest
```

The tests cover the quantale operations, circuit valuation, context keys,
counterfactual observations, evidence filtering, table lookup, controls, and
held-out application behavior.

## Current direction

The next integration step is to construct explicit CENF meta-variables from
stable, support-aware structural features and connect them to a terminating
meta-level rewrite policy followed by bounded concrete refinement. Statistical
similarity will remain separate from semantic equivalence: every graph change
must still be performed by a sound concrete ZX rewrite.

## License

This project is available under the [MIT License](LICENSE).
