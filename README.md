# ZX-CENF Transpiler

ZX-CENF is a research prototype for structure-aware optimization of quantum circuits represented as ZX diagrams. It tests whether rewrite behavior observed across a population of circuits can guide local rewrite choices on unseen circuits.

The repository combines:

- randomized ZX-calculus simplification;
- measurement of rewrite-order ambiguity;
- structural analysis of spider behavior;
- multi-objective circuit valuation; and
- learned rule selection at local rewrite crossroads.

This is a feasibility study, not a production transpiler or a complete implementation of the theoretical ZX-CENF proposal.

## How the system works

```text
QASM circuits
    -> ZX diagrams
    -> randomized rewrite exploration
    -> circuit and spider outcome measurements
    -> recurring structural contexts
    -> population-level rule preferences
    -> evaluation on held-out circuits
```

The implementation has three connected parts.

### Rewrite ambiguity analysis

Each input circuit is converted to a PyZX graph and simplified repeatedly using different seeded orders of valid rewrite passes. The resulting diagrams are extracted back into circuits and compared using:

```text
mu = (two-qubit gate count, T-count, depth)
```

Lower values are better. Variation across runs measures whether rewrite ordering affects the terminal circuit. The same runs also record which original spiders survive and how their local neighborhoods evolve.

A smaller explicit rewrite system is evaluated separately as a confluence control. It operates on a NetworkX `MultiGraph` and includes spider fusion, identity removal, self-loop deletion, and parallel Hadamard-edge cancellation.

### Structural analysis

Spider outcomes across repeated runs are represented as a spider-by-run matrix. Surviving spiders are categorized using Weisfeiler-Lehman neighborhood signatures, while removed spiders receive a separate outcome label.

Pairwise normalized mutual information measures how consistently two spiders evolve together. Agglomerative clustering on `1 - NMI` groups spiders with related outcomes. Constant-outcome spiders are identified separately because they contain no clustering information.

This analysis currently operates within each circuit. It is an empirical structural prototype, not the full cross-diagram equivalence-class construction proposed in the theoretical work.

### Population-guided rewrite selection

During training, the optimizer detects local crossroads where overlapping matches expose more than one rewrite rule. A decision context is represented by:

```text
(local structural hash, available rule set)
```

The available rule set is included because the same local topology may expose different legal choices in different graph states.

For each competing rule, training forces that rule on a graph clone, continues with the same greedy policy, and measures the final extracted circuit. The recorded improvement is:

```text
improvement = mu_before - mu_after
```

Observations are pooled across training circuits. A preference is learned only when every competing rule has sufficient evidence and the best average outcome is not tied.

At evaluation time, the optimizer looks up contexts encountered on the actual held-out trajectory. A matching learned preference can override the greedy rule choice; otherwise the optimizer falls back to greedy selection.

The valuation supports component-wise ordering and Pareto comparisons. The current experimental policy resolves rule choices lexicographically using:

```text
two-qubit count -> depth -> T-count
```

## Evaluation

Held-out circuits are evaluated against four references:

- **Greedy:** chooses the locally best improving rewrite.
- **Learned:** uses the preference table when a supported context is reached.
- **Empirical oracle:** selects the best result from several randomized rewrite orders.
- **PyZX:** applies `full_reduce` using PyZX's standard strategy.

A null-table ablation keeps the learned context keys but changes their rule assignments. This separates the effect of context coverage from the effect of the learned preferences themselves.

Synthetic motif experiments provide mechanism controls. They verify that the pipeline can learn and transfer a known preference when a recurring decision context is deliberately present. These controls validate the implementation but do not establish that useful recurrence is common in arbitrary circuits.

## Repository layout

```text
src/zx_cenf/       core implementation
experiments/       executable experiments
data/toy/          circuit generators and QASM inputs
data/*_results/    generated experimental outputs
tests/             automated tests
docs/              technical reports
```

## Requirements

- Python 3.10 or newer
- PyZX
- NetworkX
- NumPy
- pandas
- SciPy
- scikit-learn
- tqdm
- pytest and Hypothesis for development

Dependencies are declared in `pyproject.toml`. The repository uses a `src/` package layout, so the local package must be installed before running the experiments.

## Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Verify the installation:

```bash
python -c "import zx_cenf; print('zx_cenf import succeeded')"
```

Alternatively, with `uv`:

```bash
uv sync --extra dev
```

Then prefix commands with `uv run`.

## Running the experiments

Run all commands from the repository root and in the following order:

```bash
# Generate three deterministic QASM inputs.
python data/toy/generate_ambiguity_population.py

# Measure rewrite ambiguity and spider evolution.
python experiments/ambiguity/run_track1.py

# Cluster correlated spider outcomes.
python experiments/cenf/run_mi_clustering.py

# Train on circuit populations and evaluate held-out transfer.
python experiments/quantale/run_phase_f.py

# Compare learned preferences with a null policy.
python experiments/quantale/run_ablation.py

# Validate the mechanism on controlled recurring structures.
python experiments/quantale/run_positive_control.py
python experiments/quantale/run_connected_motifs.py

# Run automated tests.
python -m pytest -q
```

Generated artifacts are written to `data/track1_results/`, `data/track2_results/`, and `data/track3_results/`. The held-out transfer command prints its detailed diagnostics to the terminal.

Control experiment sizes are configurable:

```bash
python experiments/quantale/run_positive_control.py \
  --train-size 20 --test-size 10 --min-occurrences 10

python experiments/quantale/run_connected_motifs.py \
  --train-per-family 12 --test-per-family 6 --min-occurrences 8
```

## Interpreting table coverage

A learned rule can affect a held-out result only if all of the following occur:

1. the structural pattern appears in both training and held-out data;
2. the available rule set also matches;
3. every competing rule has sufficient training evidence;
4. the training outcomes produce a non-tied preference;
5. the context is reached on the held-out application trajectory; and
6. the learned choice differs from the greedy choice.

The diagnostics report these stages separately. A zero table-hit rate can therefore be interpreted as lack of recurrence, action-set mismatch, insufficient support, tied outcomes, or trajectory mismatch rather than a generic pipeline failure.

## Testing

Run the complete test suite:

```bash
python -m pytest -q
```

The tests cover the vector algebra, circuit valuation, extraction-failure handling, structural context keys, balanced counterfactual observations, preference learning, table lookup, and controlled transfer.

## Current limitations

- The full theoretical weakness functional is not implemented.
- Structural hashes are empirical context identifiers, not proven semantic equivalence classes.
- Structural clustering is not yet used as the abstraction layer for rule-table lookup.
- The empirical oracle samples a finite set of rewrite orders and is not a global optimum.
- The supplied natural circuit population is small and cannot support broad performance claims.
- Synthetic controls demonstrate mechanism feasibility, not generalization to arbitrary circuits.

## License

Licensed under the [MIT License](LICENSE).
