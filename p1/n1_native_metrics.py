"""N1候補指標の純粋関数。DCD、モデル、実験データを読む入口は持たない。"""
import numpy as np


def coordinates(value):
    """Å単位の対応済みN×3座標を検査する。単位の暗黙変換は行わない。"""
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 3 or a.shape[0] < 3 or not np.isfinite(a).all():
        raise ValueError('有限なN×3座標（N≥3）が必要です。')
    return a


def proper_rmsd(moving, reference):
    """等重みCαのproper Kabsch RMSD [Å]。行ベクトル規約、鏡映は禁止。"""
    x, y = coordinates(moving), coordinates(reference)
    if x.shape != y.shape:
        raise ValueError('原子対応と個数が一致しません。')
    x, y = x - x.mean(axis=0), y - y.mean(axis=0)
    u, _, vt = np.linalg.svd(x.T @ y)
    correction = np.eye(3)
    correction[-1, -1] = 1 if np.linalg.det(u @ vt) >= 0 else -1
    rotation = u @ correction @ vt
    return float(np.sqrt(np.mean(np.sum((x @ rotation - y) ** 2, axis=1))))


def pair_distances(value):
    """非周期の内部距離行列 [Å]。最小像やboxを使用しない。"""
    a = coordinates(value)
    return np.linalg.norm(a[:, None, :] - a[None, :, :], axis=-1)


def native_contact_mask(reference, cutoff_A=8.0, sequence_gap=3, inclusive=False):
    """単一参照上のnative接触集合。N1主候補はgap3・厳密な8Å未満。"""
    if not np.isfinite(cutoff_A) or cutoff_A <= 0 or not isinstance(sequence_gap, int) or sequence_gap < 1:
        raise ValueError('正のcutoffと正整数の配列隔たりが必要です。')
    d = pair_distances(reference)
    eligible = np.triu(np.ones(d.shape, dtype=bool), k=sequence_gap)
    mask = eligible & ((d <= cutoff_A) if inclusive else (d < cutoff_A))
    if not mask.any():
        raise ValueError('native接触集合が空です。')
    return mask


def q_from_mask(value, mask, cutoff_A=8.0, inclusive=False):
    """固定接触集合に対するQ [0,1]。接触集合を入力構造から再定義しない。"""
    d = pair_distances(value)
    m = np.asarray(mask, dtype=bool)
    if m.shape != d.shape or not m.any() or np.any(np.tril(m)):
        raise ValueError('非空の上三角native接触maskが必要です。')
    if not np.isfinite(cutoff_A) or cutoff_A <= 0:
        raise ValueError('cutoffが不正です。')
    contacts = (d <= cutoff_A) if inclusive else (d < cutoff_A)
    return float(contacts[m].mean())


def consensus_mask(contact_observations, eligible, minimum_fraction=0.75):
    """独立に固定した参照集合の占有率mask。Bhowmik原定義との同一性は保証しない。"""
    a = np.asarray(contact_observations)
    e = np.asarray(eligible, dtype=bool)
    if a.ndim != 3 or len(a) == 0 or a.shape[1:] != e.shape or a.dtype != np.bool_:
        raise ValueError('非空のboolean参照接触集合と対応maskが必要です。')
    if not 0 < minimum_fraction <= 1 or np.any(np.tril(e)):
        raise ValueError('占有率または上三角の定義が不正です。')
    mask = e & (a.mean(axis=0) >= minimum_fraction)
    if not mask.any():
        raise ValueError('共識native接触集合が空です。')
    return mask


def best_so_far(values, eligible):
    """品質・時刻適格点だけの累積最小値。最初の適格点以前はNaNを返す。"""
    r = np.asarray(values, dtype=float)
    ok = np.asarray(eligible, dtype=bool)
    if r.ndim != 1 or r.shape != ok.shape or not np.isfinite(r[ok]).all() or np.any(r[ok] < 0):
        raise ValueError('適格RMSDとmaskが不正です。')
    result = np.minimum.accumulate(np.where(ok, r, np.inf))
    result[np.isinf(result)] = np.nan
    return result


def observed_hits(times_ps, rmsd_A, q_values, eligible, rmsd_threshold_A=None,
                  q_threshold=None):
    """固定閾値の標本時刻hitと連続滞在。欠測を橋渡しせず、単点滞在は0 ps。"""
    t, r, q = (np.asarray(x, dtype=float) for x in (times_ps, rmsd_A, q_values))
    ok = np.asarray(eligible, dtype=bool)
    if t.ndim != 1 or not len(t) or any(x.shape != t.shape for x in (r, q, ok)):
        raise ValueError('同じ長さの非空一次元配列が必要です。')
    if not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
        raise ValueError('標本時刻は有限かつ厳密な昇順が必要です。')
    if not np.isfinite(r[ok]).all() or not np.isfinite(q[ok]).all() or np.any(r[ok] < 0) or np.any((q[ok] < 0) | (q[ok] > 1)):
        raise ValueError('適格標本のRMSD/Qが不正です。')
    if rmsd_threshold_A is None:
        raise ValueError('未承認の閾値を暗黙に設定できません。')
    if not np.isfinite(rmsd_threshold_A) or rmsd_threshold_A < 0:
        raise ValueError('RMSD閾値が不正です。')
    if q_threshold is not None and (not np.isfinite(q_threshold) or not 0 <= q_threshold <= 1):
        raise ValueError('Q閾値が不正です。')
    hit = ok & (r <= rmsd_threshold_A)
    if q_threshold is not None:
        hit &= q >= q_threshold
    ids = np.flatnonzero(hit)
    episodes = []
    for group in np.split(ids, np.flatnonzero(np.diff(ids) != 1) + 1):
        if len(group):
            episodes.append((int(group[0]), int(group[-1]), float(t[group[-1]] - t[group[0]])))
    return {'first_hit_ps': float(t[ids[0]]) if len(ids) else None,
            'right_censored': not bool(len(ids)), 'episodes': episodes,
            'total_observed_dwell_ps': sum(x[2] for x in episodes)}
