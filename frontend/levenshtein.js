//
// This file has is an auto-generated conversion of levensthein.py using ChatGPT (GPT4)
//

class OpType {
    static NOOP = 0;
    static DELETE = 1;
    static INSERT = 2;
    static SUBSTITUTE = 3;
}

class Op {
    constructor(type, from_idx, to_idx, from_seq, to_seq, delta) {
        this.type = type;
        this.from_idx = from_idx;
        this.to_idx = to_idx;
        this.from_seq = from_seq;
        this.to_seq = to_seq;
        this.delta = delta;
    }
}

function create2DArray(rows, columns, defaultValue) {
    let arr = new Array(rows);
    for (let i = 0; i < rows; i++) {
        arr[i] = new Array(columns).fill(defaultValue);
    }
    return arr;
}

function argMin(array) {
    if (array.length === 0) {
        return -1;
    }
    let min = array[0];
    let minIdx = 0;
    for (let i = 1; i < array.length; i++) {
        if (array[i] < min) {
            min = array[i];
            minIdx = i;
        }
    }
    return minIdx;
}

function weightedLevenshtein(from_seq, to_seq, substitution_cost, insert_cost, delete_cost, return_ops = false) {
    let from_len = from_seq.length, to_len = to_seq.length;
    let d = create2DArray(from_len + 1, to_len + 1, 0);
    let best_ops = create2DArray(from_len + 1, to_len + 1, 0);

    for (let from_idx = 0; from_idx < from_len; from_idx++) {
        let cost = delete_cost ? delete_cost(from_seq[from_idx], from_idx) : 1.0;
        d[from_idx+1][0] = d[from_idx][0] + cost;
        best_ops[from_idx+1][0] = 1;
    }

    for (let to_idx = 0; to_idx < to_len; to_idx++) {
        let cost = insert_cost ? insert_cost(to_seq[to_idx], from_idx) : 1.0;
        d[0][to_idx+1] = d[0][to_idx] + cost;
        best_ops[0][to_idx+1] = 2;
    }

    for (let from_idx = 0; from_idx < from_len; from_idx++) {
        for (let to_idx = 0; to_idx < to_len; to_idx++) {
            let subst_cost = substitution_cost ? substitution_cost(from_seq[from_idx], to_seq[to_idx], from_idx, to_idx) : 
                            (from_seq[from_idx] === to_seq[to_idx] ? 0.0 : 1.0);
            let del_cost = delete_cost ? delete_cost(from_seq[from_idx], from_idx) : 1.0;
            let ins_cost = insert_cost ? insert_cost(to_seq[to_idx], from_idx) : 1.0;

            let op_costs = [
                d[from_idx][to_idx + 1] + del_cost,
                d[from_idx + 1][to_idx] + ins_cost,
                d[from_idx][to_idx] + subst_cost,
            ];
            let min_op = argMin(op_costs);
            best_ops[from_idx + 1][to_idx + 1] = min_op + 1;
            d[from_idx + 1][to_idx + 1] = op_costs[min_op];
        }
    }

    if (return_ops) {
        let ops = getLevenshteinOps(d, best_ops, from_seq, to_seq);
        return {distance: d[from_len][to_len], ops: ops};
    }

    return {distance: d[from_len][to_len]};
}

function getLevenshteinOps(dist_matrix, best_ops, from_seq, to_seq, debug = false) {
    let from_idx = dist_matrix.length - 1, to_idx = dist_matrix[0].length - 1;
    let ops = [];

    while (true) {
        let best_dist = (from_idx - 1 >= 0 && to_idx - 1 >= 0) ? dist_matrix[from_idx - 1][to_idx - 1] : Infinity;
        let best_op = best_ops[from_idx][to_idx];
        let del_dist = (from_idx - 1 >= 0) ? dist_matrix[from_idx - 1][to_idx] : Infinity;
        let ins_dist = (to_idx - 1 >= 0) ? dist_matrix[from_idx][to_idx - 1] : Infinity;
        let subst_dist = (from_idx - 1 >= 0 && to_idx - 1 >= 0) ? dist_matrix[from_idx - 1][to_idx - 1] : Infinity;

        let best_delta = 0.0;
        if (best_op === OpType.DELETE) {
            best_delta = dist_matrix[from_idx][to_idx] - del_dist;
        } else if (best_op === OpType.INSERT) {
            best_delta = dist_matrix[from_idx][to_idx] - ins_dist;
        } else if (best_op === OpType.SUBSTITUTE) {
            best_delta = dist_matrix[from_idx][to_idx] - subst_dist;
        }

        if (best_op === OpType.NOOP) {
            break;
        } else if (best_op === OpType.DELETE) {
            ops.unshift(new Op(best_op, from_idx - 1, from_idx - 1, from_seq, to_seq, best_delta));
            from_idx -= 1;
        } else if (best_op === OpType.INSERT) {
            ops.unshift(new Op(best_op, from_idx - 1, to_idx - 1, from_seq, to_seq, best_delta));
            to_idx -= 1;
        } else if (best_op === OpType.SUBSTITUTE) {
            if (from_idx - 1 === -1 && to_idx - 1 === -1) {
                break;
            }
            ops.unshift(new Op(best_op, from_idx - 1, to_idx - 1, from_seq, to_seq, best_delta));
            from_idx -= 1;
            to_idx -= 1;
        }
    }

    return ops;
}

function buildFromOps(ops) {
    let seq = [];
    ops.forEach(op => {
        if (op.type === OpType.INSERT || op.type === OpType.SUBSTITUTE) {
            seq.push(op.to_seq[op.to_idx]);
        }
    });
    return seq;
}
