"""Serial, causal feedback bookkeeping; this is not a workflow runtime.

All times are elapsed monotonic wall-clock seconds from the same campaign t0.
Only validated MD results enter this ledger. Training snapshots are frozen when
the task is dispatched. Publishing a model/ranking does NOT change B or A: only
dispatching an MD restart selected by that ranking adopts its model.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math


def _time(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("time must be finite nonnegative elapsed seconds")
    return float(value)


def _id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("a nonempty string ID is required")
    return value


@dataclass(frozen=True)
class ResultRecord:
    result_id: str
    available_at_s: float


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    captured_at_s: float
    results: tuple
    sha256: str

    @property
    def result_ids(self):
        return tuple(r.result_id for r in self.results)

    @property
    def latest_data_at_s(self):
        return max(r.available_at_s for r in self.results)


@dataclass(frozen=True)
class ModelPublication:
    model_version: str
    snapshot_id: str
    published_at_s: float


@dataclass(frozen=True)
class RankingPublication:
    ranking_id: str
    model_version: str
    input_result_ids: tuple
    published_at_s: float
    inference_task_id: str


@dataclass(frozen=True)
class InferenceDispatch:
    task_id: str
    model_version: str
    input_result_ids: tuple
    dispatched_at_s: float


@dataclass(frozen=True)
class FeedbackState:
    observed_at_s: float
    adopted_model_version: str | None
    adopted_ranking_id: str | None
    adopted_snapshot_id: str | None
    backlog_results: int | None
    data_age_s: float | None
    latest_model_version: str | None
    published_model_versions: tuple
    unranked_model_versions: tuple
    unused_ranking_ids: tuple

    @property
    def bootstrap(self):
        return self.adopted_model_version is None


@dataclass(frozen=True)
class Event:
    sequence: int
    at_s: float
    kind: str
    payload_json: str

    def to_dict(self):
        return {"schema_version": 1, "sequence": self.sequence, "at_s": self.at_s,
                "kind": self.kind, **json.loads(self.payload_json)}


class FeedbackLedger:
    """Called by one serialized event handler; immutable records are safe to save.

    ``events`` returns immutable events; ``to_dict`` returns an independent JSON
    object for append-only JSONL persistence by the caller. No result or event may
    be backdated. Successful writes are atomic with respect to validation errors.
    """
    def __init__(self):
        self._results = {}
        self._snapshots = {}
        self._models = {}
        self._rankings = {}
        self._inferences = {}
        self._published_inferences = set()
        self._md_ids = set()
        self._used_rankings = set()
        self._adopted_ranking = None
        self._events = []
        self._last_at = 0.0

    @property
    def events(self):
        return tuple(self._events)

    @property
    def results(self):
        return tuple(self._results.values())

    def snapshot(self, snapshot_id):
        return self._snapshots[snapshot_id]

    def _check(self, at_s):
        at_s = _time(at_s)
        if at_s < self._last_at:
            raise ValueError("events and observations must not use past state")
        return at_s

    def _emit(self, at_s, kind, **payload):
        event = Event(len(self._events), at_s, kind,
                      json.dumps(payload, sort_keys=True, allow_nan=False))
        self._events.append(event)
        self._last_at = at_s
        return event

    def result_available(self, result_id, at_s):
        at_s, result_id = self._check(at_s), _id(result_id)
        if result_id in self._results:
            raise ValueError("duplicate valid result ID")
        self._results[result_id] = ResultRecord(result_id, at_s)
        return self._emit(at_s, "md_result_available", result_id=result_id)

    def capture_snapshot(self, snapshot_id, at_s, result_ids=None):
        at_s, snapshot_id = self._check(at_s), _id(snapshot_id)
        if snapshot_id in self._snapshots:
            raise ValueError("snapshot ID is immutable and cannot be reused")
        ids = tuple(self._results) if result_ids is None else tuple(result_ids)
        if not ids or len(ids) != len(set(ids)) or any(i not in self._results for i in ids):
            raise ValueError("snapshot needs distinct, already available results")
        records = tuple(self._results[i] for i in sorted(ids))
        canonical = {"captured_at_s": at_s, "results": [asdict(r) for r in records]}
        digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        snapshot = Snapshot(snapshot_id, at_s, records, digest)
        self._snapshots[snapshot_id] = snapshot
        self._emit(at_s, "training_snapshot_captured", snapshot_id=snapshot_id,
                   snapshot_sha256=digest, results=canonical["results"])
        return snapshot

    def model_published(self, model_version, snapshot_id, at_s):
        at_s, model_version = self._check(at_s), _id(model_version)
        if model_version in self._models or snapshot_id not in self._snapshots:
            raise ValueError("model needs a unique version and existing training snapshot")
        self._models[model_version] = ModelPublication(model_version, snapshot_id, at_s)
        return self._emit(at_s, "model_published", model_version=model_version,
                          snapshot_id=snapshot_id)

    def inference_dispatched(self, task_id, model_version, input_result_ids, at_s):
        at_s, task_id = self._check(at_s), _id(task_id)
        ids = tuple(input_result_ids)
        if task_id in self._inferences or model_version not in self._models:
            raise ValueError("inference needs a unique ID and already published model")
        if not ids or len(ids) != len(set(ids)) or any(i not in self._results for i in ids):
            raise ValueError("inference inputs must be distinct, already available results")
        self._inferences[task_id] = InferenceDispatch(task_id, model_version, ids, at_s)
        return self._emit(at_s, "inference_dispatched", task_id=task_id,
                          model_version=model_version, input_result_ids=list(ids))

    def ranking_published(self, ranking_id, model_version, input_result_ids, at_s,
                          *, inference_task_id):
        at_s, ranking_id = self._check(at_s), _id(ranking_id)
        ids = tuple(input_result_ids)
        if ranking_id in self._rankings or model_version not in self._models:
            raise ValueError("ranking needs a unique ID and already published model")
        if not ids or len(ids) != len(set(ids)) or any(i not in self._results for i in ids):
            raise ValueError("ranking inputs must be distinct, available MD results")
        if inference_task_id not in self._inferences or inference_task_id in self._published_inferences:
            raise ValueError("ranking needs an unpublished, dispatched inference task")
        inference = self._inferences[inference_task_id]
        if model_version != inference.model_version or ids != inference.input_result_ids:
            raise ValueError("ranking model and input manifest must equal inference dispatch")
        self._rankings[ranking_id] = RankingPublication(ranking_id, model_version, ids, at_s,
                                                       inference_task_id)
        self._published_inferences.add(inference_task_id)
        return self._emit(at_s, "ranking_published", ranking_id=ranking_id,
                          model_version=model_version, input_result_ids=list(ids),
                          inference_task_id=inference_task_id)

    def md_dispatched(self, task_id, at_s, ranking_id=None, selected_result_id=None):
        at_s, task_id = self._check(at_s), _id(task_id)
        if task_id in self._md_ids:
            raise ValueError("MD task already dispatched")
        if ranking_id is None:
            if selected_result_id is not None:
                raise ValueError("initial restart must not claim ranking-selected data")
            if self._adopted_ranking is not None:
                raise ValueError("after first adoption every restart must name its selection lineage")
            model_version = None
        else:
            if ranking_id not in self._rankings:
                raise ValueError("cannot adopt an unpublished/future ranking")
            ranking = self._rankings[ranking_id]
            if selected_result_id not in ranking.input_result_ids:
                raise ValueError("selected restart must belong to ranking input results")
            model_version = ranking.model_version
            self._adopted_ranking = ranking_id
            self._used_rankings.add(ranking_id)
        self._md_ids.add(task_id)
        return self._emit(at_s, "md_dispatched", task_id=task_id, ranking_id=ranking_id,
                          model_version=model_version, selected_result_id=selected_result_id)

    def feedback(self, now_s):
        now_s = self._check(now_s)
        # Advance the observable frontier: future events cannot be backdated to
        # before an already computed dispatch decision.
        self._last_at = now_s
        ranked = {r.model_version for r in self._rankings.values()}
        models = tuple(self._models)
        common = dict(observed_at_s=now_s, latest_model_version=models[-1] if models else None,
                      published_model_versions=models,
                      unranked_model_versions=tuple(v for v in models if v not in ranked),
                      unused_ranking_ids=tuple(r for r in self._rankings if r not in self._used_rankings))
        if self._adopted_ranking is None:
            return FeedbackState(adopted_model_version=None, adopted_ranking_id=None,
                                 adopted_snapshot_id=None, backlog_results=None, data_age_s=None, **common)
        ranking = self._rankings[self._adopted_ranking]
        snapshot = self._snapshots[self._models[ranking.model_version].snapshot_id]
        return FeedbackState(adopted_model_version=ranking.model_version,
                             adopted_ranking_id=ranking.ranking_id,
                             adopted_snapshot_id=snapshot.snapshot_id,
                             backlog_results=len(set(self._results) - set(snapshot.result_ids)),
                             data_age_s=now_s - snapshot.latest_data_at_s, **common)
