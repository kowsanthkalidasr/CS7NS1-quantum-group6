"""
policy.py — QIS-NET Project 2 policy (Group 6, Variant 06).

The policy decides, each time a fresh pair arrives on a link, what to do:
swap, purify, hold, or discard aged pairs.

Our policy: FreshestPairPolicy
  1. Safety floor  - discard any stored pair whose current fidelity has fallen
                     to <= 0.5 (it carries no distillable entanglement).
  2. Swap freshest - whenever both links of a chain hold a pair, swap the
                     FRESHEST pair on each side (index -1), not the oldest.
  3. Cap fast link - keep at most `keep_fast` pairs on the faster link of the
                     chain; older surplus pairs are discarded. The faster link
                     refills quickly, so stale pairs there are never needed.
  4. Protect the bottleneck - pairs on the slower link are never capped, so
                     every bottleneck pair gets used (rate is capped by it).
  Optional (off by default, used in our experiments): purify on the fast link.

AI-assistant declaration: drafted with the help of Claude (Anthropic);
reviewed, tested and adapted by Group 6.
"""


class BaselinePolicy:
    """Swap-as-soon-as-possible; never purify. PROVIDED as the baseline.
    It meets the reference scenarios' expectations but is deliberately
    insufficient for most variant SLOs. Kept because run_two_hop uses it."""

    def __init__(self, params):
        self.params = params
        # map each repeater node to its adjacent link pairs for swapping
        self.chains = params["policy"]["swap_chains"]  # list of [left, right]

    def on_pair_ready(self, link, pair, state, sim):
        for left, right in self.chains:
            if state.pairs.get(left) and state.pairs.get(right):
                sim.swap(left, right)


class FreshestPairPolicy:
    """Group 6 policy: freshest-pair swapping with a capped fast-link buffer.

    Parameters (defaults are what the autograder uses via make_policy):
      keep_fast   - max pairs stored on the faster link of each chain
      floor       - discard pairs whose current fidelity is <= this value
      purify_fast - if True (and allowed), purify on the faster link
    """

    def __init__(self, params, keep_fast=1, floor=0.5, purify_fast=False):
        self.params = params
        self.keep_fast = max(1, int(keep_fast))
        self.floor = floor
        self.purify_fast = purify_fast
        self.chains = [tuple(c) for c in
                       params.get("policy", {}).get("swap_chains", [])]
        # Work out the faster link of each chain from the parameters,
        # so the policy still works if the link speeds are swapped round.
        self.fast_link = {chain: self._faster_link(chain, params)
                          for chain in self.chains}

    @staticmethod
    def _faster_link(chain, params):
        """Return the link id in `chain` with the higher pair-generation
        rate (attempt_rate * p_success)."""
        links = params.get("topology", {}).get("links", [])

        def gen_rate(link_id):
            if 0 <= link_id < len(links):
                lp = links[link_id]
                return lp.get("attempt_rate", 0.0) * lp.get("p_success", 0.0)
            return 0.0

        left, right = chain
        return left if gen_rate(left) > gen_rate(right) else right

    # ------------------------------------------------------------ main hook

    def on_pair_ready(self, link, pair, state, sim):
        for chain in self.chains:
            left, right = chain
            fast = self.fast_link[chain]

            # 1. Clean up: remove pairs that have decayed past usefulness.
            self._drop_below_floor(left, state, sim)
            self._drop_below_floor(right, state, sim)

            # 2. Deliver: swap the freshest pair on each side.
            if state.pairs.get(left) and state.pairs.get(right):
                sim.swap(left, right, left_index=-1, right_index=-1)

            # 3. Optional: purify surplus pairs on the fast link.
            if self.purify_fast and state.purification_allowed:
                self._maybe_purify(fast, state, sim)

            # 4. Cap the fast link's buffer (discard the oldest surplus).
            inv = state.pairs.get(fast, [])
            while len(inv) > self.keep_fast:
                sim.discard(fast, 0)

    # ------------------------------------------------------------ helpers

    def _drop_below_floor(self, link_id, state, sim):
        """Discard every pair on link_id whose fidelity is <= floor.
        Walk backwards so removing index i does not shift earlier ones."""
        inv = state.pairs.get(link_id, [])
        for i in range(len(inv) - 1, -1, -1):
            if state.current_fidelity(inv[i]) <= self.floor:
                sim.discard(link_id, i)

    @staticmethod
    def _maybe_purify(link_id, state, sim):
        """Purify the two oldest pairs on link_id, but only when there are
        two of them and both are above 0.5 (otherwise BBPSSW cannot help)."""
        inv = state.pairs.get(link_id, [])
        if len(inv) < 2:
            return
        if min(state.current_fidelity(inv[0]),
               state.current_fidelity(inv[1])) > 0.5:
            sim.purify(link_id)


def make_policy(params):
    """Return the policy object used by the autograder."""
    return FreshestPairPolicy(params)
