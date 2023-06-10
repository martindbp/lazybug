from __future__ import annotations
import math
import unittest
from typing import *
from enum import IntEnum
from dataclasses import dataclass, field

import numpy as np


class OpType(IntEnum):
    NOOP = 0
    DELETE = 1
    INSERT = 2
    SUBSTITUTE = 3


@dataclass
class Op:
    type: OpType
    from_idx: int
    to_idx: int
    from_seq: Sequence = field(repr=False)
    to_seq: Sequence = field(repr=False)
    delta: float


SubstitutionCostFunction = Callable[[Any, Any, int, int], float]
InsertCostFunction = Callable[[Any, int], float]
DeleteCostFunction = Callable[[Any, int], float]


def weighted_levenshtein(
    from_seq: Sequence,
    to_seq: Sequence,
    substitution_cost: Optional[SubstitutionCostFunction] = None,
    insert_cost: Optional[SubstitutionCostFunction] = None,
    delete_cost: Optional[DeleteCostFunction] = None,
    return_ops=False,
) -> Tuple[float, Optional[List[Op]]]:
    """
    Returns the Levenshtein distance between `from_seq` and `to_seq` weighted by
    the `substitution_cost` function
    """
    from_len, to_len = len(from_seq), len(to_seq)
    d = np.zeros((from_len + 1, to_len + 1), dtype=np.float64)
    for from_idx in range(from_len):
        cost = (1.0 if delete_cost is None else delete_cost(from_seq[from_idx], from_idx))
        d[from_idx+1, 0] = d[from_idx, 0] + cost

    for to_idx in range(to_len):
        d[0, to_idx+1] = d[0, to_idx] + (1.0 if insert_cost is None else insert_cost(to_seq[to_idx], from_idx))

    best_ops = np.zeros((from_len + 1, to_len + 1), dtype=np.int64)
    best_ops[1 : from_len + 1, 0] = 1
    best_ops[0, 1 : to_len + 1] = 2
    for from_idx in range(from_len):
        for to_idx in range(to_len):
            # NOTE: it's less confusing to keep two sets of indices,
            # from/to_idx for the sequence, and d_from/to_idx for the
            # corresonding indices in the distance matrix
            d_from_idx = from_idx + 1
            d_to_idx = to_idx + 1
            if substitution_cost is None:
                subst_cost = 0.0 if from_seq[from_idx] == to_seq[to_idx] else 1.0
            else:
                subst_cost = substitution_cost(from_seq[from_idx], to_seq[to_idx], from_idx, to_idx)

            del_cost = 1.0 if delete_cost is None else delete_cost(from_seq[from_idx], from_idx)
            ins_cost = 1.0 if insert_cost is None else insert_cost(to_seq[to_idx], from_idx)

            op_costs = np.array([
                d[d_from_idx - 1, d_to_idx]     + del_cost,
                d[d_from_idx, d_to_idx - 1]     + ins_cost,
                (d[d_from_idx - 1, d_to_idx - 1] + subst_cost),
            ])
            min_op = np.argmin(op_costs)
            best_ops[d_from_idx, d_to_idx] = min_op + 1  # +1 to get 1-3 range
            d[d_from_idx, d_to_idx] = op_costs[min_op]

    if return_ops:
        ops = get_levenshtein_ops(d, best_ops, from_seq, to_seq)
        return d[-1, -1], ops

    return d[-1, -1]


def get_levenshtein_ops(
    dist_matrix: DistMatrix,
    best_ops: BestOpsMatrix,
    from_seq: Sequence,
    to_seq: Sequence,
    debug: bool = False,
) -> List[Op]:
    if debug:
        path_matrix = dist_matrix.copy()

    from_idx, to_idx = dist_matrix.shape[0] - 1, dist_matrix.shape[1] - 1
    ops: List[Op] = []

    while True:
        best_dist = dist_matrix[from_idx - 1, to_idx - 1] if from_idx - 1 >= 0 and to_idx - 1 >= 0 else float("inf")
        best_op = OpType(best_ops[from_idx, to_idx])
        del_dist = dist_matrix[from_idx - 1, to_idx] if from_idx - 1 >= 0 else float("inf")
        ins_dist = dist_matrix[from_idx, to_idx - 1] if to_idx - 1 >= 0 else float("inf")
        subst_dist = dist_matrix[from_idx - 1, to_idx - 1] if from_idx - 1 >= 0 and to_idx - 1 >= 0 else float("inf")
        best_delta = 0.0
        if best_op == OpType.DELETE:
            best_delta = dist_matrix[from_idx, to_idx] - del_dist
        elif best_op == OpType.INSERT:
            best_delta = dist_matrix[from_idx, to_idx] - ins_dist
        elif best_op == OpType.SUBSTITUTE:
            best_delta = dist_matrix[from_idx, to_idx] - subst_dist

        if best_op == OpType.NOOP:
            break
        elif best_op == OpType.DELETE:
            ops.insert(0, Op(best_op, from_idx - 1, from_idx - 1, from_seq, to_seq, best_delta))
            if debug:
                path_matrix[from_idx, to_idx] = 0
            from_idx -= 1
        elif best_op == OpType.INSERT:
            ops.insert(0, Op(best_op, from_idx - 1, to_idx - 1, from_seq, to_seq, best_delta))
            if debug:
                path_matrix[from_idx, to_idx] = 0
            to_idx -= 1
        elif best_op == OpType.SUBSTITUTE:
            if from_idx - 1 == -1 and to_idx - 1 == -1:
                break  # We've reached the beginning
            ops.insert(0, Op(best_op, from_idx - 1, to_idx - 1, from_seq, to_seq, best_delta))
            if debug:
                path_matrix[from_idx, to_idx] = 0
            from_idx -= 1
            to_idx -= 1

    if debug:
        # For printing a matrix
        old_precision = np.get_printoptions()["precision"]  # type: ignore
        np.set_printoptions(precision=1)  # type: ignore
        if max(len(from_seq), len(to_seq)) < 15:
            print(dist_matrix)
            print(path_matrix)
            print(best_ops)
        for op in ops:
            if op.type == "delete":
                if op.delta > 0:
                    print(f"{op.from_idx}: {from_seq[op.to_idx]} -> x {op.delta:.1f}")
                else:
                    print(f"{op.from_idx}: {from_seq[op.to_idx]} -> x")
            elif op_type == "insert":
                if delta > 0:
                    print(f"{op.from_idx}: x <- {to_seq[op.from_idx]} {op.delta:.1f}")
                else:
                    print(f"{op.from_idx}: x <- {to_seq[op.from_idx]}")
            else:
                if delta > 0:
                    print(f"{op.from_idx}: {from_seq[op.to_idx]} -> {to_seq[op.from_idx]} {op.delta:.1f}")
                else:
                    print(f"{op.from_idx}: {from_seq[op.to_idx]} -> {to_seq[op.from_idx]}")
        np.set_printoptions(precision=old_precision)  # type: ignore

    return ops


def build_from_ops(ops: List[Op]) -> Sequence:
    seq = []
    for op in ops:
        if op.type in [OpType.INSERT, OpType.SUBSTITUTE]:
            seq.append(op.to_seq[op.to_idx])
        elif op.type == OpType.DELETE:
            pass  # we just don't append it

    return seq


class TestLevenshtein(unittest.TestCase):

    def test_levenshtein(self):
        self.assertEqual(weighted_levenshtein('a', 'aaaaa'), 4)
        self.assertEqual(weighted_levenshtein('aaaaa', 'a'), 4)

        self.assertEqual('foo'.upper(), 'FOO')
        s1 = 'hello ok world?'
        s2 = 'we hello world!'
        dist, ops = weighted_levenshtein(s1, s2, return_ops=True)
        self.assertEqual(dist, 7)
        self.assertEqual(''.join(build_from_ops(ops)), s2)

        def _subst_cost(from_val, to_val, *args):
            if from_val == to_val:
                return 0.0
            if from_val == '?' and to_val == '!':
                return 0.5
            return 1.0

        dist = weighted_levenshtein(s1, s2, _subst_cost)
        self.assertEqual(dist, 6.5)

        def _insert_cost(ins_val, *args):
            if ins_val in ['w', ' ']:
                return 0.8
            return 1.0

        dist, ops = weighted_levenshtein(s1, s2, _subst_cost, _insert_cost, return_ops=True)
        self.assertEqual(''.join(build_from_ops(ops)), s2)
        self.assertAlmostEqual(dist, 6.1)  # almost for floating point equality

        def _delete_cost(del_val, *args):
            if del_val == 'k':
                return 0.7
            return 1.0

        dist, ops = weighted_levenshtein(s1, s2, _subst_cost, _insert_cost, _delete_cost, return_ops=True)
        self.assertEqual(''.join(build_from_ops(ops)), s2)

        self.assertAlmostEqual(dist, 5.8)  # almost for floating point equality


        # Now let's make the insert operation very expensive, and check that all ops become substitutions
        def _insane_insert_cost(del_val, *args):
            return 100.0

        dist, ops = weighted_levenshtein(s1, s2, _subst_cost, _insane_insert_cost, _delete_cost, return_ops=True)
        for op in ops:
            self.assertEqual(op.type, OpType.SUBSTITUTE)


        # Check that if we set a high substitution cost, all the ops will be insert/delete
        def _insane_subst_cost(*args):
            return 100.0

        dist, ops = weighted_levenshtein(s1, s2, _insane_subst_cost, _insert_cost, _delete_cost, return_ops=True)
        for op in ops:
            self.assertNotEqual(op.type, OpType.SUBSTITUTE)



if __name__ == '__main__':
    unittest.main()
