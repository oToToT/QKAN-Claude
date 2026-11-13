"""Training / evaluation loops shared by all experiments."""

from __future__ import annotations

import copy
import math
import time

import numpy as np
import torch
from torch import nn


def mse(model: nn.Module, x: torch.Tensor, y: torch.Tensor, batch: int = 2048) -> float:
    model.eval()
    tot = 0.0
    with torch.no_grad():
        for i in range(0, len(x), batch):
            tot += ((model(x[i : i + batch]) - y[i : i + batch]) ** 2).sum().item()
    return tot / y.numel()


def fit(
    model: nn.Module,
    train: tuple[torch.Tensor, torch.Tensor],
    evals: dict[str, tuple[torch.Tensor, torch.Tensor]],
    *,
    epochs: int = 50,
    batch_size: int = 4,
    lr: float = 1e-3,
    schedule: str = "constant",
    seed: int = 0,
    loss_fn=None,
    select_on: str | None = None,
    eval_every: int = 1,
    weight_decay: float = 0.0,
) -> dict:
    """Adam training following the paper's protocol.

    Args:
        schedule: ``'constant'`` (paper) or ``'cosine'`` (per-step cosine decay
            of the learning rate to zero over the same number of epochs).
        select_on: name of an eval split; if given, the returned ``best`` entry
            reports all metrics at the epoch with the lowest loss on that split
            and the model is restored to that checkpoint.
    """
    x_tr, y_tr = train
    gen = torch.Generator().manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    steps_per_epoch = math.ceil(len(x_tr) / batch_size)
    total = epochs * steps_per_epoch
    sched = None
    if schedule == "cosine":
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, total)
    elif schedule != "constant":
        raise ValueError(schedule)
    if loss_fn is None:
        loss_fn = lambda pred, target: ((pred - target) ** 2).mean()  # noqa: E731

    history = {k: [] for k in evals}
    history["train_loss"] = []
    best = None
    best_state = None
    t0 = time.time()
    for epoch in range(epochs):
        model.train()
        perm = torch.randperm(len(x_tr), generator=gen)
        running = 0.0
        for i in range(0, len(x_tr), batch_size):
            idx = perm[i : i + batch_size]
            loss = loss_fn(model(x_tr[idx]), y_tr[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            if sched is not None:
                sched.step()
            running += loss.item() * len(idx)
        history["train_loss"].append(running / len(x_tr))
        if (epoch + 1) % eval_every == 0 or epoch == epochs - 1:
            metrics = {k: mse(model, *v) for k, v in evals.items()}
            for k, v in metrics.items():
                history[k].append(v)
            if select_on is not None and (best is None or metrics[select_on] < best[select_on]):
                best = dict(metrics, epoch=epoch + 1)
                best_state = copy.deepcopy(model.state_dict())
        if not np.isfinite(history["train_loss"][-1]):
            break
    final = {k: history[k][-1] for k in evals}
    if best_state is not None:
        model.load_state_dict(best_state)
    return {"final": final, "best": best, "history": history, "seconds": time.time() - t0}
