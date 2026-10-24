"""Derive bounded S2 evidence; never changes input runs or selects thresholds."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

from .science import sha256_file, write_json_new


def physical_features(positions):
    """Nonperiodic intramolecular CA distances, Å; exclude sequence separation<3."""
    import numpy as np
    xyz = np.asarray(positions, dtype=np.float64)
    if xyz.shape[-2:] != (28, 3) or not np.isfinite(xyz).all():
        raise ValueError("Expected finite (...,28,3) CA coordinates")
    i, j = np.triu_indices(28, k=3)
    return np.linalg.norm(xyz[..., i, :] - xyz[..., j, :], axis=-1)


def coverage(features, widths, contact_cutoff):
    import numpy as np
    f = np.asarray(features)
    if f.ndim != 2 or not len(f) or not np.isfinite(f).all() or (f < 0).any():
        raise ValueError("Expected nonempty finite nonnegative distance matrix")
    if not widths or any(w <= 0 for w in widths) or contact_cutoff <= 0:
        raise ValueError("Thresholds must be positive and fixed before comparison")
    result = {"frames": len(f), "pair_count": f.shape[1],
              "contact_fingerprint_states": int(len(np.unique(f < contact_cutoff, axis=0))),
              "distance_bin_states": {str(w): int(len(np.unique(np.floor(f / w), axis=0))) for w in widths},
              "distance_angstrom_min_max": [float(f.min()), float(f.max())]}
    return result


def selection_comparison(before, after, shortlist_size):
    import numpy as np
    from scipy.stats import spearmanr
    key = lambda r: (r["result_id"], r["frame"])
    if [key(r) for r in before] != [key(r) for r in after]:
        raise ValueError("Candidate pools/order differ; cannot attribute ranking to a model change")
    b = sorted(before, key=lambda r: (r["lof"], *key(r)))[:shortlist_size]
    a = sorted(after, key=lambda r: (r["lof"], *key(r)))[:shortlist_size]
    sb, sa = {key(r) for r in b}, {key(r) for r in a}
    final_b = sorted(b, key=lambda r: (r["rmsd_angstrom"], r["lof"], *key(r)))
    final_a = sorted(a, key=lambda r: (r["rmsd_angstrom"], r["lof"], *key(r)))
    def frame(r):
        return {"result_id": r["result_id"], "frame": r["frame"], "rmsd_angstrom": r["rmsd_angstrom"]}
    return {"candidate_count": len(before), "shortlist_size": min(shortlist_size, len(before)),
            "lof_shortlist_intersection": len(sb & sa), "lof_shortlist_jaccard": len(sb & sa) / len(sb | sa),
            "lof_score_spearman": float(spearmanr([r["lof"] for r in before], [r["lof"] for r in after]).statistic),
            "lof_only_top1_changed": key(b[0]) != key(a[0]),
            "actual_reference_guided_top1_changed": key(final_b[0]) != key(final_a[0]),
            "final_order_equal": [key(r) for r in final_b] == [key(r) for r in final_a],
            "lof_only_before_after_top1": [frame(b[0]), frame(a[0])],
            "reference_guided_before_after_top1": [frame(final_b[0]), frame(final_a[0])],
            "reference_only_top1": frame(min(before, key=lambda r: (r["rmsd_angstrom"], *key(r)))),
            "rmsd_values_identical": bool(np.array_equal([r["rmsd_angstrom"] for r in before], [r["rmsd_angstrom"] for r in after])),
            "scientific_benefit_evaluated": False}


def analyze(run_dir, output):
    import numpy as np
    import MDAnalysis as mda
    from MDAnalysis.analysis import align, distances
    import torch
    run, out = Path(run_dir), Path(output)
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((run / "manifest.json").read_text())
    checksums = json.loads((run / "checksums.json").read_text())
    for path, expected in checksums.items():
        if sha256_file(run / path) != expected:
            raise ValueError(f"Raw artifact changed: {path}")
    tasks = {p.parent.name: json.loads(p.read_text()) for p in (run / "tasks").glob("*/result.json")}
    timings, stability, feature_sets = [], [], []
    cfg0 = json.loads(next((run / "tasks").glob("*/request.json")).read_text())["science_config"]
    for name, r in sorted(tasks.items()):
        internal = sum(t["wall_time_s"] for t in r["component_timing"]["stages"])
        if abs(internal - r["wall_time_s"]) > 1e-7:
            raise ValueError("Task timing partition failed")
        dispatch = json.loads((run / "tasks" / name / "dispatch.json").read_text())
        timings.append({"task": name, "type": r["task_type"], "seed": r["seed"],
                        "worker_internal_s": r["wall_time_s"], **dispatch,
                        "component_stages": r["component_timing"]["stages"],
                        "physical_md_ns": r.get("physical_simulation_ns"),
                        "frames": r.get("frames"), "training_frames": r.get("training_frames")})
        if r["task_type"] != "simulation":
            continue
        traj = mda.Universe(r["pdb_path"], r["dcd_path"])
        ref_path = json.loads((run / "tasks" / name / "request.json").read_text())["inputs"]["reference_pdb"]
        ref = mda.Universe(ref_path)
        ca = traj.select_atoms("protein and name CA")
        positions = np.array([ca.positions.copy() for _ in traj.trajectory])
        f = physical_features(positions)
        feature_sets.append((name, f))
        with (Path(r["output_dir"]) / "sim.log").open() as s:
            log = list(csv.reader(s))
        headers, values = log[0], np.array(log[1:], dtype=float)
        if not np.isfinite(values).all() or len(values) != r["frames"]:
            raise ValueError("MD state log nonfinite or incomplete")
        temp = values[:, next(i for i, s in enumerate(headers) if "Temperature" in s)]
        energy = values[:, next(i for i, s in enumerate(headers) if "Potential" in s)]
        saved = np.load(r["contact_map_path"], allow_pickle=True)
        # Reproduce upstream alignment and box semantics, compare against no-box.
        align.AlignTraj(traj, ref, select="protein and name CA", in_memory=True).run()
        box = traj.atoms.dimensions
        mismatch_nonperiodic, mismatch_periodic = 0, 0
        for index, _ in enumerate(traj.trajectory):
            vector = saved[index]
            matrix = np.zeros((28, 28), dtype=bool)
            n = len(vector) // 2
            matrix[np.asarray(vector[:n], dtype=int), np.asarray(vector[n:], dtype=int)] = True
            xyz = traj.select_atoms("protein and name CA").positions
            nonperiodic = distances.contact_matrix(xyz, cutoff=8.0, box=None)
            periodic = distances.contact_matrix(xyz, cutoff=8.0, box=box)
            mismatch_nonperiodic += int(not np.array_equal(matrix, nonperiodic))
            mismatch_periodic += int(not np.array_equal(matrix, periodic))
        stability.append({"task": name, "frames": r["frames"], "atoms": traj.atoms.n_atoms,
                          "all_coordinates_finite": bool(np.isfinite(positions).all()),
                          "temperature_K_min_mean_max": [float(temp.min()), float(temp.mean()), float(temp.max())],
                          "potential_kJ_mol_min_max": [float(energy.min()), float(energy.max())],
                          "analysis_box_angstrom_degrees": box.tolist() if box is not None else None,
                          "saved_contact_frames_differ_from_nonperiodic": mismatch_nonperiodic,
                          "saved_contact_frames_differ_from_periodic": mismatch_periodic,
                          "equilibration_or_sampling_convergence_established": False})
    def load_scores(name):
        return json.loads((run / "tasks" / name / "science" / "candidate-scores.json").read_text())
    comparison = selection_comparison(load_scores("infer-frozen-r0"), load_scores("infer-updated-r0"), cfg0["num_outliers"])
    before, updated = tasks["train-before"], tasks["train-updated"]
    if updated["parent_checkpoint_sha256"] != before["model_weight_sha256"]:
        raise ValueError("Update did not start from common checkpoint")
    frozen_a = torch.load(before["model_weight_path"], map_location="cpu", weights_only=True)
    updated_a = torch.load(updated["model_weight_path"], map_location="cpu", weights_only=True)
    change_norm = sum(float(((frozen_a["model_state_dict"][k].double() - v.double())**2).sum())
                      for k, v in updated_a["model_state_dict"].items())**0.5
    comparison.update(parent_checkpoint_sha256=updated["parent_checkpoint_sha256"],
                      frozen_checkpoint_unchanged=sha256_file(before["model_weight_path"]) == before["model_weight_sha256"],
                      frozen_model_id=before["model_id"], updated_model_id=updated["model_id"],
                      training_frames_before_after=[before["training_frames"], updated["training_frames"]],
                      training_result_ids_before_after=[before["training_result_ids"], updated["training_result_ids"]],
                      checkpoint_epochs_before_after=[frozen_a["epoch"], updated_a["epoch"]],
                      weight_difference_l2=change_norm,
                      common_candidate_snapshot=tasks["infer-frozen-r0"]["inference_snapshot_id"] == tasks["infer-updated-r0"]["inference_snapshot_id"])
    for label in ("frozen", "updated"):
        comparison[label + "_same_seed_repeated_scores_equal"] = load_scores(f"infer-{label}-r0") == load_scores(f"infer-{label}-r1")
        comparison[label + "_same_seed_repeated_embeddings_equal"] = bool(np.array_equal(
            np.load(run / "tasks" / f"infer-{label}-r0" / "science/embeddings.npy"),
            np.load(run / "tasks" / f"infer-{label}-r1" / "science/embeddings.npy")))
    start = time.perf_counter()
    options = manifest["coverage_proposal_frozen_before_results"]
    metric = {name: coverage(f, options["distance_bin_widths_angstrom"], options["contact_threshold_angstrom"])
              for name, f in feature_sets}
    allfeatures = np.concatenate([f for _, f in feature_sets])
    metric["all_pilot_frames"] = coverage(allfeatures, options["distance_bin_widths_angstrom"], options["contact_threshold_angstrom"])
    metric["duplicating_same_frames_changes_counts"] = (coverage(np.concatenate([allfeatures, allfeatures]),
                options["distance_bin_widths_angstrom"], options["contact_threshold_angstrom"])["distance_bin_states"]
                != metric["all_pilot_frames"]["distance_bin_states"])
    metric["evaluation_wall_s_excludes_trajectory_loading"] = time.perf_counter() - start
    write_json_new(out / "costs.json", timings)
    with (out / "costs.csv").open("x") as s:
        keys = ["task", "type", "seed", "worker_internal_s", "dispatch_to_result_s", "supervised_child_s", "physical_md_ns", "frames", "training_frames"]
        writer = csv.DictWriter(s, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(timings)
    write_json_new(out / "stability.json", stability)
    write_json_new(out / "model-comparison.json", comparison)
    write_json_new(out / "coverage-computability.json", metric)
    write_json_new(out / "validation.json", {"verified_raw_files": len(checksums), "tasks": len(tasks),
                    "timing_partitions_pass": True, "evaluation_ready": False,
                    "evidence_type": "local CPU/GPU measurement", "status": "MEASURED"})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    analyze(args.run, args.output)
