"""Historical dispatch candidates plus a single-GPU engineering FIFO.

The external Colmena/Parsl executor owns submission, completion and resource
accounting. ``choose`` is a pure selector: call serially and immediately move the
selected task from ready to running before asking for a second GPU decision.
Durations and thresholds must be frozen from development measurements; no
scientific-quality oracle, sleeps, training triggers or preemption are used here.
"""
from dataclasses import dataclass, asdict
import math

from .events import FeedbackState


POLICIES = ("Static-reservation-matched", "Task-aware-F0", "Feedback-first", "Feedback-gated-F1")
ENGINEERING_POLICIES = ("Single-GPU-FIFO",)
KINDS = ("md", "train", "infer")


def _finite(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f"{name} must be finite and {'positive' if positive else 'nonnegative'}")


@dataclass(frozen=True)
class Task:
    task_id: str
    kind: str
    ready_at_s: float
    estimated_s: float
    cpu_cores: int = 1
    model_version: str | None = None
    snapshot_id: str | None = None
    ranking_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.task_id, str) or not self.task_id.strip() or self.kind not in KINDS:
            raise ValueError("task needs a nonempty stable ID and known kind")
        _finite(self.ready_at_s, "ready_at_s")
        _finite(self.estimated_s, "estimated_s", True)
        if type(self.cpu_cores) is not int or self.cpu_cores < 1:
            raise ValueError("cpu_cores must be a positive integer")
        if self.kind == "infer" and not self.model_version:
            raise ValueError("inference must name its published model")


@dataclass(frozen=True)
class PolicyConfig:
    name: str
    horizon_s: float
    wait_cap_s: float
    backlog_threshold: int
    age_threshold_s: float
    md_estimate_s: float
    inference_estimate_s: float
    static_roles: tuple = ((0, "md"), (1, "learning"))
    gpu_slots: int = 2

    def __post_init__(self):
        if self.name not in POLICIES + ENGINEERING_POLICIES:
            raise ValueError("unknown policy name")
        if type(self.gpu_slots) is not int or self.gpu_slots not in (1, 2):
            raise ValueError("gpu_slots must name one or two real execution devices")
        if self.name == "Static-reservation-matched" and self.gpu_slots != 2:
            raise ValueError("Static-reservation-matched requires two distinct GPUs")
        if self.name == "Single-GPU-FIFO" and self.gpu_slots != 1:
            raise ValueError("Single-GPU-FIFO is an engineering order for exactly one GPU")
        for k in ("horizon_s", "wait_cap_s", "age_threshold_s", "md_estimate_s", "inference_estimate_s"):
            _finite(getattr(self, k), k, True)
        if type(self.backlog_threshold) is not int or self.backlog_threshold < 1:
            raise ValueError("backlog_threshold must be positive integer")
        roles = dict(self.static_roles)
        if len(roles) != len(self.static_roles) or set(roles.values()) != {"md", "learning"}:
            raise ValueError("static_roles needs distinct GPU IDs and MD/learning reservations")


@dataclass(frozen=True)
class Decision:
    task: Task | None
    reason: str
    gated: bool
    feedback: FeedbackState
    excluded: tuple = ()

    def to_dict(self):
        return {"task_id": self.task.task_id if self.task else None,
                "reason": self.reason, "gated": self.gated,
                "feedback": asdict(self.feedback), "excluded": list(self.excluded)}


def choose(ready_tasks, *, running_tasks=(), feedback, now_s, gpu_id,
           available_cpu_cores, config):
    """Choose one task for one verified free whole GPU; never submit it here.

    Guard order: legality/horizon -> overdue FIFO -> MD progress -> shared
    bootstrap -> policy. Overdue work wins over the MD progress preference so a
    single available GPU cannot starve learning indefinitely. MD progress prefers
    an MD if none is running; it is not a guarantee that one MD is always running.
    Static reservations remain hard constraints, including during bootstrap.
    Single-GPU-FIFO instead chooses the oldest legal request, without bootstrap
    or MD-priority overrides; it is only a closed-loop engineering order.
    """
    _finite(now_s, "now_s")
    if type(available_cpu_cores) is not int or available_cpu_cores < 0:
        raise ValueError("available_cpu_cores must be nonnegative integer")
    if feedback.observed_at_s != now_s:
        raise ValueError("feedback must be observed at this decision time")
    if feedback.bootstrap != (feedback.backlog_results is None and feedback.data_age_s is None):
        raise ValueError("bootstrap must use NA for both B and A")
    if not feedback.bootstrap:
        if type(feedback.backlog_results) is not int or feedback.backlog_results < 0:
            raise ValueError("B must be a nonnegative count")
        _finite(feedback.data_age_s, "A")
    ready, running = tuple(ready_tasks), tuple(running_tasks)
    all_ids = [t.task_id for t in ready + running]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("ready/running tasks must have unique, disjoint IDs")
    if any(t.ready_at_s > now_s for t in running):
        raise ValueError("running task cannot originate in the future")
    role_map = dict(config.static_roles)
    if gpu_id not in role_map or gpu_id not in range(config.gpu_slots):
        raise ValueError("GPU is outside the frozen device set")
    if len(running) >= config.gpu_slots:
        return Decision(None, "gpu_capacity_full", False, feedback)
    if now_s >= config.horizon_s:
        return Decision(None, "horizon_reached", False, feedback)
    excluded, legal = [], []
    busy_kinds = {t.kind for t in running if t.kind != "md"}
    for task in ready:
        reason = None
        if task.ready_at_s > now_s:
            reason = "not_yet_ready"
        elif task.cpu_cores > available_cpu_cores:
            reason = "insufficient_cpu"
        elif task.kind in busy_kinds:
            reason = "same_learning_kind_running"
        elif task.kind == "infer" and task.model_version not in feedback.published_model_versions:
            reason = "model_not_published"
        elif config.name == "Static-reservation-matched" and ((role_map[gpu_id] == "md") != (task.kind == "md")):
            reason = "static_reservation"
        elif task.kind != "md":
            chain = task.estimated_s + config.md_estimate_s
            if task.kind == "train":
                chain += config.inference_estimate_s
            if now_s + chain > config.horizon_s:
                reason = "estimated_feedback_chain_exceeds_horizon"
        if reason:
            excluded.append((task.task_id, reason))
        else:
            legal.append(task)
    excluded = tuple(sorted(excluded))
    if not legal:
        return Decision(None, "no_legal_task", False, feedback, excluded)

    def f0(tasks):
        return min(tasks, key=lambda t: (-(now_s - t.ready_at_s) / t.estimated_s, t.task_id))

    def done(task, reason, gated=False):
        return Decision(task, reason, gated, feedback, excluded)

    if config.name == "Single-GPU-FIFO":
        return done(min(legal, key=lambda t: (t.ready_at_s, t.task_id)), "single_gpu_engineering_fifo")
    overdue = [t for t in legal if now_s - t.ready_at_s >= config.wait_cap_s]
    if overdue:
        return done(min(overdue, key=lambda t: (t.ready_at_s, t.task_id)), "common_wait_guard")
    md = [t for t in legal if t.kind == "md"]
    if config.gpu_slots > 1 and md and not any(t.kind == "md" for t in running):
        return done(f0(md), "common_md_progress")
    learning = [t for t in legal if t.kind != "md"]
    if feedback.bootstrap and learning:
        # A first model's inference completes the initial feedback chain.
        infer = [t for t in learning if t.kind == "infer"]
        return done(f0(infer or learning), "common_bootstrap")
    if config.name == "Feedback-first" and learning:
        infer = [t for t in learning if t.kind == "infer"]
        return done(f0(infer or learning), "learning_priority")
    gate = (not feedback.bootstrap and
            (feedback.backlog_results >= config.backlog_threshold or feedback.data_age_s >= config.age_threshold_s))
    if config.name == "Feedback-gated-F1" and gate and learning:
        unranked = [t for t in learning if t.kind == "infer" and t.model_version in feedback.unranked_model_versions]
        train = [t for t in learning if t.kind == "train"]
        return done(f0(unranked or train or learning), "feedback_gate", True)
    return done(f0(legal), "task_aware_f0")
