import unittest

from levenshtein import weighted_levenshtein, build_from_ops, OpType


class TestLevenshtein(unittest.TestCase):

    def test_levenshtein(self):
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
