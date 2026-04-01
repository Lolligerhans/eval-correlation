import chess.pgn
import re
import numpy as np


def extract_wv(comment):
    """Extract the 'wv' value from a move comment string."""
    assert comment
    if not comment:
        return None
    match = re.search(r"wv=([-+]?\d+\.?\d*)", comment)
    if match:
        return float(match.group(1))
    assert False
    return None


def is_book_move(comment):
    """Check if the move comment indicates a book move."""
    assert comment
    return comment and "book" in comment


# TODO: I believe the current implementation has the variance normalization
#       implicitly within the correlation computation.
def normalize_sequence(vals):
    """
    vals: list of floats.
    Returns the normalized sequence: first remove linear trend (first -> last),
    then scale to unit variance.
    """
    n = len(vals)
    assert n >= 2
    if n < 2:
        return None
    first, last = vals[0], vals[-1]
    step = last - first
    trend = [first + step * i / (n - 1) for i in range(n)]
    detrended = [v - t for v, t in zip(vals, trend)]
    std = np.std(detrended)
    if std == 0:
        return np.zeros(n)  # all constant after detrending
    return np.array(detrended) / std


# TODO: Possibly normalize correlation by number of overlapping positions
def cross_correlation(w, b, max_lag=10):
    """
    Compute Pearson correlation between w and b for lags -max_lag..+max_lag.
    Returns the lag that maximizes the correlation.
    """
    assert len(w) == len(b)
    n = len(w)
    assert n > 12  # Logic may not work otherwise
    max_lag = min(10, n - 1)
    if n != len(b):
        # Presumably needed for implementation. Not needed mathematically.
        raise ValueError("Lengths of w and b must be equal")
    best_lag = 0
    best_corr = -np.inf
    for lag in range(-max_lag, max_lag + 1):
        # As in the 2nd equivalent formulation on Wikipedia:
        #   lag >= 0:
        #       Move white sequence to the right
        #   lag < 0:
        #       Move white sequence to the left
        if lag >= 0:
            if n - lag == 0:
                continue
            w_slice = w[0 : n - lag]
            b_slice = b[lag:n]
        else:
            pos_lag = -lag
            if n - pos_lag == 0:
                continue
            w_slice = w[pos_lag:n]
            b_slice = b[0 : n - pos_lag]
        # Pearson correlation coefficient
        assert len(w_slice) >= 2
        if len(w_slice) < 2:
            continue
        # FIXME: What does corrcoef do? Is that what we want it to do?
        corr = np.corrcoef(w_slice, b_slice)[0, 1]
        assert corr
        if np.isnan(corr):
            continue
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    return best_lag


def process_game(game):
    """Extract evaluation sequences and compute cross-correlation lag."""
    white_elo = int(game.headers.get("WhiteElo", 0))
    black_elo = int(game.headers.get("BlackElo", 0))
    assert white_elo != 0
    assert black_elo != 0
    elo_diff: int = white_elo - black_elo

    # Traverse the mainline moves
    node = game
    white_vals = []
    black_vals = []

    while node.variations:
        node = node.variation(0)  # take main line
        comment = node.comment
        if not comment:
            continue
        if is_book_move(comment):
            continue  # skip book moves entirely
        # Not a book move: use it
        wv = extract_wv(comment)
        assert wv
        if wv is None:
            continue  # no evaluation, skip
        # Determine side: ply is 1-indexed
        ply = node.ply()
        if ply % 2 == 1:  # white's move
            white_vals.append(wv)
        else:  # black's move
            black_vals.append(wv)
        # if abs(wv) > 4.0:
        if abs(white_vals[-1] > 4.0) and abs(black_vals[-1] > 4.0):
            break

    # If we didn't get any moves, skip
    assert white_vals
    assert black_vals
    if not white_vals or not black_vals:
        return None, None

    # Trim to equal length (drop extra from the side that made the last move)
    min_len = min(len(white_vals), len(black_vals))
    assert min_len >= 12
    if min_len < 2:
        return None, None
    white_vals = white_vals[:min_len]
    black_vals = black_vals[:min_len]

    # Normalize
    w_norm = normalize_sequence(white_vals)
    b_norm = normalize_sequence(black_vals)
    assert w_norm
    assert b_norm
    if w_norm is None or b_norm is None:
        return None, None

    # Compute best lag
    lag = cross_correlation(w_norm, b_norm)
    return lag, elo_diff


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python script.py games.pgn")
        sys.exit(1)
    filename = sys.argv[1]

    pos_lags = []
    neg_lags = []

    with open(filename) as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
            lag, elo_diff = process_game(game)
            assert lag is not None
            assert elo_diff is not None
            if lag is not None:
                if elo_diff > 0:
                    pos_lags.append(lag)
                elif elo_diff < 0:
                    neg_lags.append(lag)
                else:
                    # Equal elo is likely a processing error. If it happens and is legit just ignore it. The correlation in that case would be meaningless.
                    assert False

    avg_pos = np.mean(pos_lags) if pos_lags else float("nan")
    avg_neg = np.mean(neg_lags) if neg_lags else float("nan")

    print(f"Average maximal correlation position (positive Elo diff): {avg_pos:.2f}")
    print(f"Average maximal correlation position (negative Elo diff): {avg_neg:.2f}")
    print(
        "When white is better (positive difference), then we expect a positive position to be maximal because the white engine finds the correct line first"
    )


if __name__ == "__main__":
    main()
