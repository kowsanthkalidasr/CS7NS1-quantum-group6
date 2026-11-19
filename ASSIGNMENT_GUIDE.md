# QIS-NET Project 2: Quantum Entanglement Distribution Network Simulation
**Module:** Scalable Computing (Quantum) — Trinity College Dublin  
**Assigned Variant:** Group 6 — Variant 06  
**Assessment Weight:** 40% of Module Grade (24% Autograded Code + 16% Technical Report)  
**Deliverables:** `simulator.py`, `policy.py`, `experiments.py`, `experiment_results.json`, and an 8-page Technical Report (PDF)

---

## 1. Executive Summary & File Inventory

This project requires designing, simulating, and evaluating an **autonomous network policy** for distributing quantum entanglement across a linear repeater network under realistic physical noise, memory decoherence, and probabilistic operations.

### File Structure & Responsibilities

| File | Status / Action | Description & Requirements |
| :--- | :--- | :--- |
| [`qnetsim.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/qnetsim.py) | **READ-ONLY**<br>*(Do not modify)* | The discrete-event simulation engine. The autograder runs its own pristine copy. Contains event queues, Poisson link generation, exponential decay, swapping, and BBPSSW purification. |
| [`variant_params.json`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/variant_params.json) | **READ-ONLY**<br>*(Reference config)* | Specific parameters assigned to Group 6: link attempt rates, success probabilities, physical gate/memory fidelities, arrival workload, and strict Service Level Objectives (SLOs). |
| [`simulator.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/simulator.py) | **EDIT**<br>*(Complete TODOs)* | Implement the three entry points called by the autograder:<br>1. `run_one_hop`<br>2. `run_two_hop`<br>3. `run_variant_scenario` (including FIFO request-to-inventory matching). |
| [`policy.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/policy.py) | **EDIT**<br>*(Replace baseline)* | Implement an intelligent link policy replacing `BaselinePolicy`. Must decide when to swap, purify, buffer, or discard pairs to meet all Variant 06 SLOs. |
| [`experiments.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/experiments.py) | **EDIT**<br>*(Complete TODOs)* | Implement `run_sensitivity` to conduct a One-At-a-Time (OAT) parameter sweep of memory coherence time ($T_2$) against delivered rate, computing 95% Student's t confidence intervals and writing `experiment_results.json`. |
| [`READ_ME_FIRST.txt`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/READ_ME_FIRST.txt) | **REFERENCE** | Basic instructions and pointer to module specification. |

---

## 2. Quantum Networking Basics & Mathematical Foundations

### 2.1 The Need for Entanglement Distribution
Classical networks copy data across routers. In quantum networks, the **No-Cloning Theorem** prevents duplicating arbitrary quantum states:
$$\forall |\psi\rangle, \quad |\psi\rangle \otimes |0\rangle \not\to |\psi\rangle \otimes |\psi\rangle$$
To transmit quantum information or establish secure cryptographic keys (QKD) across long distances, nodes must pre-share maximally entangled Bell pairs, typically:
$$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$$
Distributed states can then be utilized via **quantum teleportation** or **entanglement-based QKD (E91 / BBM92)**.

### 2.2 Werner States and State Fidelity
Noise in optical channels and quantum memories transforms pure Bell states into mixed states. A standard isotropic depolarized state (Werner state) is represented as:
$$\rho = F |\Phi^+\rangle\langle\Phi^+| + \frac{1 - F}{3} \left( |\Phi^-\rangle\langle\Phi^-| + |\Psi^+\rangle\langle\Psi^+| + |\Psi^-\rangle\langle\Psi^-| \right)$$
The **fidelity** $F \in [0, 1]$ measures the overlap with the ideal target state:
$$F = \langle \Phi^+ | \rho | \Phi^+ \rangle$$
- $F = 1.0$: Pure Bell pair.
- $F = 0.5$: Classical limit; below or equal to 0.5, no distillable entanglement exists.
- $F = 0.25$: Completely mixed 2-qubit state ($I/4$).

### 2.3 Memory Decoherence: Depolarizing Decay ($T_2$)
Quantum memories suffer from phase and energy relaxation. Under depolarizing noise with characteristic spin-spin coherence time $T_2$ (in ms), the fidelity of a pair born with initial fidelity $F_0$ decays over time $\Delta t$ toward the unpolarized floor ($0.25$):
$$F(\Delta t) = 0.25 + (F_0 - 0.25) \exp\left(-\frac{\Delta t}{T_2}\right)$$
> **Crucial Insight:** Decoherence does *not* erase or drop the physical photon pair from memory. The pair remains in inventory, but its quantum information degrades continuously toward $0.25$. Storing pairs without swapping or refreshing will poison the end-to-end fidelity!

### 2.4 Entanglement Swapping (Quantum Repeater)
Direct transmission of photons over optical fiber decays exponentially with distance. Quantum repeaters divide distance into elementary links:
1. Two adjacent links $(0, 1)$ and $(1, 2)$ generate independent entangled pairs.
2. Intermediate repeater Node 1 performs a **Bell State Measurement (BSM)** on its two local qubits.
3. Node 1 broadcasts the 2 classical measurement bits.
4. After feed-forward corrections, an entangled pair is established between distant endpoints $(0, 2)$.

**Harness Swapping Model:**
- **Success probability:** Swapping is non-deterministic, succeeding with probability $q_{swap}$.
- **Output fidelity:** Approximated in the harness by the product rule:
  $$F_{out} = F_{left} \cdot F_{right} \cdot F_{swap}$$
  *(where $F_{left}$ and $F_{right}$ are the time-decayed fidelities of the two constituent pairs at the moment of swap, and $F_{swap}$ is the gate quality factor).*
- **Consumption:** Consumes 2 elementary pairs regardless of whether the swap succeeds or fails.

### 2.5 Entanglement Purification / Distillation (BBPSSW Protocol)
When channel noise degrades pair fidelity, two lower-fidelity pairs on the same link can be combined using local operations and classical communication (LOCC) to yield one pair of higher fidelity.

Using the BBPSSW recurrence protocol on two identical Werner pairs of fidelity $F$:
1. Parameterize error $e = \frac{1 - F}{3}$.
2. The purification succeeds with probability:
   $$P_{succ} = F^2 + 2Fe + 5e^2$$
3. If successful, the resulting pair has improved fidelity:
   $$F' = \frac{F^2 + e^2}{P_{succ}}$$
- **Trade-off:** Consumes 2 input pairs to produce at most 1 output pair. If $F \le 0.5$, purification cannot improve fidelity ($F' \le F$).

### 2.6 Link Generation Processes & Rate Analytics
Each elementary link $i$ operates an independent Poisson attempt process:
- Attempt rate: $a_i$ (attempts per millisecond).
- Success probability per attempt: $p_i$.
- Successful generation rate: $\lambda_i = 1000 \cdot a_i \cdot p_i$ (pairs per second).
- Inter-arrival time between successful pairs: exponentially distributed with mean $\frac{1}{\lambda_i}$.

**Throughput Across a Repeater Chain:**
- **Continuous Generation with Buffering ($T_2 = \infty$, $q_{swap}=1$):**
  The long-run throughput is limited by the bottleneck link:
  $$\text{Rate}_{ref} = \min(\lambda_1, \lambda_2, \dots, \lambda_k)$$
- **With Swap Probability $q_{swap}$:**
  $$\text{Rate} \approx q_{swap} \cdot \min(\lambda_1, \lambda_2)$$

---

## 3. Group 6 / Variant 06 Anatomy & Parameter Analysis

From [`variant_params.json`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/variant_params.json):

### 3.1 Physical & Topology Parameters
```json
"physics": {
  "f_link": 0.9146,
  "f_swap": 0.9891,
  "t2_ms": 220.7,
  "q_swap": 0.864,
  "purification_allowed": true
}
```
- Chain topology: `Node 0 <--- Link 0 ---> Node 1 <--- Link 1 ---> Node 2`
- **Link 0 (Nodes 0–1):**
  - Attempt rate $a_0 = 4.0641 \text{ ms}^{-1}$
  - Success probability $p_0 = 0.00707$
  - Effective generation rate:
    $$\lambda_0 = 4.0641 \times 0.00707 \times 1000 \approx \mathbf{28.733} \text{ pairs/sec}$$
- **Link 1 (Nodes 1–2):**
  - Attempt rate $a_1 = 4.5625 \text{ ms}^{-1}$
  - Success probability $p_1 = 0.0281$
  - Effective generation rate:
    $$\lambda_1 = 4.5625 \times 0.0281 \times 1000 \approx \mathbf{128.206} \text{ pairs/sec}$$

### 3.2 The Severe Asymmetry Bottleneck
Notice that **Link 1 is ~4.46 times faster than Link 0**:
- Link 0 produces 1 pair every ~34.8 ms.
- Link 1 produces 1 pair every ~7.8 ms.
- The bottleneck link is Link 0 ($\lambda_{bottleneck} = 28.733 \text{ pairs/sec}$).
- Maximum possible theoretical swap rate:
  $$28.733 \times q_{swap} = 28.733 \times 0.864 = \mathbf{24.825} \text{ pairs/sec}$$

### 3.3 Workload & Service Level Objectives (SLOs)
```json
"workload": {
  "arrival_rate_per_s": 24.7,
  "endpoints": [[0, 2]]
},
"slo": {
  "min_rate": 19.6,
  "min_fidelity": 0.7769,
  "max_p95_latency_ms": 573.25
}
```

### 3.4 Why the Baseline Policy Fails
In [`variant_params.json`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/variant_params.json), the calibration metrics show:
- `baseline_policy`:
  - `rate`: **26.04 pairs/s** (Meets $\ge 19.6$)
  - `mean_fidelity`: **0.2324** (**DISASTROUS FAILURE**, target is $\ge 0.7769$)
  - `p95_latency_ms`: **381.50 ms** (Meets $\le 573.25$)

#### Diagnostic Cause of Failure:
The `BaselinePolicy` executes:
```python
if state.pairs.get(left) and state.pairs.get(right):
    sim.swap(left, right)
```
1. `sim.swap(left, right)` defaults to `left_index=0, right_index=0` (the **oldest** pair in each buffer).
2. Because Link 1 produces pairs over 4 times faster than Link 0, pairs on Link 1 accumulate in a long FIFO queue.
3. By the time a Link 1 pair reaches index 0 to be swapped, it has sat in memory for hundreds of milliseconds.
4. Since $T_2 = 220.7 \text{ ms}$, after $220\text{–}600 \text{ ms}$, its fidelity has decayed almost completely to the $0.25$ floor!
5. Swapping a decayed Link 1 pair with a Link 0 pair results in:
   $$F_{out} = F_0 \cdot F_1 \cdot F_{swap} \approx 0.91 \cdot 0.25 \cdot 0.989 \approx \mathbf{0.23}$$
6. **Conclusion:** To pass, your policy must manage queue lengths, discard stale pairs, select freshest pairs, or purify!

---

## 4. What the Professor Wants You to Do (Detailed Requirements)

You must implement solutions in three Python files.

```
       Assignment 2 Directory
 ┌──────────────────────────────────┐
 │ READ_ME_FIRST.txt                │
 │ variant_params.json              │
 │ qnetsim.py (DO NOT TOUCH)        │
 ├──────────────────────────────────┤
 │ simulator.py                     │ <--- Complete 3 functions
 │ policy.py                        │ <--- Replace BaselinePolicy
 │ experiments.py                   │ <--- Complete run_sensitivity
 └──────────────────────────────────┘
```

### 4.1 Task 1: Complete `simulator.py`
You must complete three entry points with exact signatures:

#### 1. `run_one_hop(params, sim_time_ms, seed) -> dict`
- **Objective:** Simulate a single elementary link (no swapping, no repeaters).
- **Setup:**
  - Build links via `make_links(params, which="one_hop")`.
  - Initialize `Simulator(links=links, t2=params['physics']['t2_ms'], q_swap=1.0, f_swap=1.0, purification_allowed=False, seed=seed)`.
  - Record generated pairs as delivered (since `qnetsim` only populates `delivered` on swap).
  - You can track deliveries with a small inline callback/policy or by recording pairs in `on_pair_ready`.
- **Expected Return:**
  ```python
  {"rate": float, "mean_fidelity": float}
  ```
  *(For Variant 06, expected rate is $\approx 28.733$ pairs/s, fidelity $\approx 0.9146$).*

#### 2. `run_two_hop(params, sim_time_ms, seed) -> dict`
- **Objective:** Reference scenario for two links with ideal repeater conditions.
- **Setup:**
  - Build links via `make_links(params, which="two_hop")`.
  - Reference parameters: $T_2 = \infty$ (`math.inf`), $q_{swap} = 1.0$, $F_{swap} = \text{params['physics']['f_swap']}$, `purification_allowed = False`.
  - Use an immediate-swap policy (`BaselinePolicy` or equivalent) that swaps whenever both Link 0 and Link 1 have at least one pair.
  - Summarize results using `qnetsim.summarise`.
- **Expected Return:**
  ```python
  {"rate": float, "mean_fidelity": float}
  ```
  *(For Variant 06, expected rate $\approx 28.733$ pairs/s, fidelity $\approx 0.8274$).*

#### 3. `run_variant_scenario(params, sim_time_ms, seed, policy) -> dict`
- **Objective:** Execute the full variant topology under real noise and evaluate against the request workload.
- **Setup:**
  - Build links via `make_links(params, which="variant")`.
  - Initialize `Simulator` with exact physics from `params['physics']`:
    - `t2 = params['physics']['t2_ms']`
    - `q_swap = params['physics']['q_swap']`
    - `f_swap = params['physics']['f_swap']`
    - `purification_allowed = params['physics']['purification_allowed']`
    - `seed = seed`
  - Run simulator for `sim_time_ms` with the provided `policy`.
  - Generate deterministic request arrival times using `request_times(params, sim_time_ms, seed)`.
  - **Workload / Request-to-Inventory FIFO Matching:**
    - The delivered pairs form an inventory buffer (ordered by `delivered_at`).
    - Incoming requests (ordered by arrival time $t_{req}$) are matched 1-to-1 against delivered pairs (ordered by $t_{deliv}$).
    - **Latency Calculation:**
      - If pair $j$ was delivered *before or at* request $j$'s arrival ($t_{deliv, j} \le t_{req, j}$), the pair was waiting in buffer:
        $$\text{latency}_j = 0.0 \text{ ms}$$
      - If pair $j$ was delivered *after* request $j$'s arrival ($t_{deliv, j} > t_{req, j}$), the request had to wait:
        $$\text{latency}_j = t_{deliv, j} - t_{req, j}$$
      - Compute $p95$ latency over **served requests only**:
        $N_{served} = \min(\text{len}(requests), \text{len}(delivered))$.
        Sort served latencies and pick the 95th percentile.
        *(If no requests served, $p95 = \infty$).*
    - **Resource Efficiency:**
      $$\text{pairs\_consumed\_per\_delivery} = \frac{\text{state.stats}['generated']}{\max(1, \text{len}(delivered))}$$
- **Expected Return:**
  ```python
  {
      "rate": float,
      "mean_fidelity": float,
      "p95_latency_ms": float,
      "pairs_consumed_per_delivery": float
  }
  ```

---

### 4.2 Task 2: Design `policy.py`
You must replace `BaselinePolicy` with your own policy class and return it from `make_policy(params)`.

#### Policy Interface:
```python
class CustomPolicy:
    def __init__(self, params):
        self.params = params
        ...

    def on_pair_ready(self, link, pair, state, sim):
        # Triggered every time a new pair is successfully generated on 'link'
        ...
```

#### Tools & Actions Available in `sim`:
1. `sim.swap(left_link_id, right_link_id, left_index=..., right_index=...)`:
   - Consumes one pair from each link.
   - **Tip:** Default indices are `0` (oldest). Passing `-1` or `len(inv)-1` selects the **freshest** pair!
2. `sim.purify(link_id)`:
   - Consumes the two oldest pairs on `link_id`. If successful, adds one higher-fidelity pair.
   - Only permitted if `state.purification_allowed == True`.
3. `sim.discard(link_id, index=0)`:
   - Removes stale pair from buffer, incrementing `stats['discarded']`.
4. `state.current_fidelity(pair)`:
   - Computes current decayed fidelity of a pair at `state.now`.

#### Policy Design Strategies to Beat Variant 06 SLOs:
Recall Group 6 targets:
- Rate $\ge 19.6$
- Mean fidelity $\ge 0.7769$
- p95 latency $\le 573.25$

| Technique | How It Works | Benefit for Group 6 |
| :--- | :--- | :--- |
| **Buffer Cap / Queue Limiting** | Keep at most 2–4 pairs on Link 1. If buffer exceeds cap, discard oldest. | Prevents Link 1 pairs from sitting in memory for hundreds of ms. |
| **Freshest-Pair Swapping (LIFO)** | Swap using `left_index=-1, right_index=-1` or highest fidelity. | Uses pairs with minimal decay time $\Delta t$, boosting $F_{out}$. |
| **Decay Floor Discarding** | Check `state.current_fidelity(p)` before swapping; if $F(t) < F_{cutoff}$ (e.g. 0.88), discard it. | Guarantees swapped pairs meet minimum fidelity threshold. |
| **Targeted Purification** | On Link 1 (which has high excess rate ~128/s), purify two pairs to create pristine pairs ($F > 0.94$). | Leverages excess Link 1 capacity to dramatically raise fidelity without starving the bottleneck Link 0! |

---

### 4.3 Task 3: Implement `experiments.py`
You must implement `run_sensitivity(params, seeds) -> dict`.

#### Experiment Goals:
Perform a **One-At-a-Time (OAT) parameter sensitivity sweep** measuring how memory coherence time ($T_2$) impacts delivered rate.
- Grid: `params['experiment']['t2_grid_ms']` = `[55.2, 110.3, 220.7, 441.4, 882.8]` ms.
- Seeds: First $N$ seeds from `params['experiment']['seeds']` ($N = \text{seeds\_per\_point} = 5$).
- For each grid point $T_2$:
  1. Make a deep copy of `params`.
  2. Set `params_copy['physics']['t2_ms'] = t2`.
  3. Create your policy: `pol = make_policy(params_copy)`.
  4. For each seed, execute `run_variant_scenario(params_copy, params_copy['grading']['sim_time_ms'], seed, pol)`.
  5. Collect the `rate` metric across all runs.
  6. Compute mean and 95% Confidence Interval half-width using the provided `mean_ci95(rates)`:
     $$h = t_{0.975, n-1} \cdot \frac{s}{\sqrt{n}}$$
- Write output to `experiment_results.json` and return the dictionary.

#### Required Output JSON Schema:
```json
{
  "parameter": "t2_ms",
  "grid": [55.2, 110.3, 220.7, 441.4, 882.8],
  "seeds_per_point": 5,
  "points": [
    {
      "t2_ms": 55.2,
      "rate_mean": 24.12,
      "rate_ci95": 1.25,
      "n_seeds": 5
    },
    ...
  ]
}
```

---

## 5. Grading Rubric & Assessment Breakdown

Total Course Weight: **40% of the entire module**.

```
                Total Project Mark (40%)
               /                        \
    Autograded Code (24%)          Technical Report (16%)
    - API Compliance: 10%          - 8 pages maximum
    - Ref Validation: 25%          - Mathematical vs Empirical
    - Determinism:    10%          - Protocol & Trade-off Analysis
    - SLO Targets:    25%          - Sensitivity Discussion
    - Robustness:     10%          - Limitations & Synthesis
    - Sensitivity:    20%
```

### Detailed Breakdown of Code Marks (24% of module):
1. **API Compliance (10%):** Exact return types, dictionary keys, function signatures in `simulator.py` and `experiments.py`.
2. **Reference Validation (25%):** Accurate outputs for `run_one_hop` and `run_two_hop` matching analytic models within tolerances (`rate_rel: 0.08`, `fid_abs: 0.01`).
3. **Determinism (10%):** Given the same random seed, repeated simulation runs produce identical results.
4. **SLO Fulfillment (25%):** Meeting or exceeding all three variant SLOs (`min_rate`, `min_fidelity`, `max_p95_latency_ms`) on held-out test seeds.
5. **Robustness (10%):** Graceful handling of edge cases (empty inventories, extreme noise, short runs).
6. **Sensitivity Experiment (20%):** Valid `experiment_results.json` adhering to schema and proper Student's t 95% CI reporting.

### Technical Report (16% of module, max 8 pages):
- **Introduction & Architecture:** Physical model, repeater nodes, Werner states, depolarizing noise.
- **Protocol Engineering:** Detailed rationale for your policy (buffering limits, purification vs swapping trade-offs).
- **Validation:** Plot and compare one-hop and two-hop simulations against analytical formulas.
- **SLO Evaluation:** Comparison table between Baseline Policy and your Custom Policy across rate, fidelity, latency, and consumption.
- **Sensitivity Analysis:** Plots of Rate vs. $T_2$ with error bars ($95\%$ CI), explaining asymptotic behavior and memory saturation.
- **Model Limitations:** Discuss what the simulator abstracts away (instantaneous operations, absence of classical propagation delay, simplified swap product proxy).

---

## 6. Critical Pitfalls to Avoid

> [!WARNING]
> 1. **Do not modify `qnetsim.py`:** The autograder brings its own unmodified `qnetsim.py`. Any changes in local `qnetsim.py` will not exist on the grading server.
> 2. **Do not mix up `p95_delivery_time_ms` and `p95_latency_ms`:**
>    - `qnetsim.summarise()` returns `p95_delivery_time_ms`, which is the 95th percentile of absolute simulation clock timestamps at delivery.
>    - The project requires `p95_latency_ms`, which is the request queue wait time: $\max(0, t_{deliv} - t_{req})$.
> 3. **Unserved Requests in Latency:** Do not include unserved requests when computing the 95th percentile latency (they would skew latency to infinity).
> 4. **Purification Rule Check:** Always check `state.purification_allowed` before calling `sim.purify()`.
> 5. **Reproducibility & Seed Generation:** Use `np.random.default_rng(seed)` or derived seeds as specified in starter code; do not use global random state.
> 6. **Package Restrictions:** Only standard library and `numpy` are permitted. Do **not** import `qiskit`, `scipy`, `pandas`, or external networking libraries.

---

## 7. Immediate Next Steps for Implementation

1. **Test Environment:** Verify Python 3.10 + NumPy environment execution.
2. **Implement Reference Tasks:** Fill in `run_one_hop` and `run_two_hop` in [`simulator.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/simulator.py) and test against reference values in `variant_params.json`.
3. **Implement Workload Buffer:** Complete FIFO queue matching in `run_variant_scenario`.
4. **Develop Custom Policy:** Iterate on [`policy.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/policy.py) using queue trimming and freshest-pair swapping to conquer the Link 1 bottleneck and pass the $F \ge 0.7769$ threshold.
5. **Run Sensitivity Sweep:** Implement `run_sensitivity` in [`experiments.py`](file:///d:/Trinity/Scalable%20Computing%20(Quantum)/Assignment%202/experiments.py) to produce `experiment_results.json`.
