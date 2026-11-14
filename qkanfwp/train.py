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
    grad_clip: float | None = None,
) -> dict:
    """Adam training following the paper's protocol.

    Args:
        schedule: ``'constant'`` (paper) or ``'cosine'`` (per-step cosine decay
            of the learning rate to zero over the same number of epochs).
        select_on: name of an eval split; if given, the returned ``best`` entry
            reports all metrics at the epoch with the lowest loss on that split
            and the model is restored to that checkpoint.
        grad_clip: if given, clip the global gradient norm to this value.
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
            if grad_clip is not None:
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
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


def fit_history(
    model: nn.Module,
    train: tuple[torch.Tensor, torch.Tensor],
    evals: dict[str, tuple[torch.Tensor, torch.Tensor]],
    *,
    epochs: int = 50,
    batch_size: int = 4,
    lr: float = 1e-3,
    schedule: str = "constant",
    seed: int = 0,
    eval_every: int = 1,
    grad_clip: float | None = None,
) -> dict:
    """Training of a model whose read-out is solved from a labelled history
    (``ObservableMemoryFWP`` with ``memory='history'``).

    Every optimiser step is one forecasting episode inside the training
    windows, which are in chronological order: the windows before a random cut
    are the labelled history, the observable is solved from them in closed
    form, and the loss is the error on the windows after the cut.  The number
    of optimiser steps equals that of the mini-batch protocol
    (``epochs * ceil(n / batch_size)``).  For evaluation the observable is
    solved from all training windows and kept fixed.
    """
    x_tr, y_tr = train
    n = len(x_tr)
    gen = torch.Generator().manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    steps_per_epoch = math.ceil(n / batch_size)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs * steps_per_epoch) if schedule == "cosine" else None
    ahead = max(n // 4, 1)  # the test part is a fifth of the series: forecast about that far past the cut
    history = {k: [] for k in evals}
    history["train_loss"] = []
    t0 = time.time()
    for epoch in range(epochs):
        model.train()
        running = 0.0
        for _ in range(steps_per_epoch):
            cut = int(torch.randint(n // 3, n - 1, (1,), generator=gen))
            k = model.query_features(x_tr)
            r = model.history_observable(k[:cut], y_tr[:cut, 0])
            pred = (k[cut : cut + ahead] @ r) * model.y_scale
            loss = ((pred - y_tr[cut : cut + ahead, 0]) ** 2).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            if grad_clip is not None:
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            opt.step()
            if sched is not None:
                sched.step()
            running += loss.item()
        history["train_loss"].append(running / steps_per_epoch)
        if (epoch + 1) % eval_every == 0 or epoch == epochs - 1:
            model.fit_history(x_tr, y_tr)
            for name, v in evals.items():
                history[name].append(mse(model, *v))
        if not np.isfinite(history["train_loss"][-1]):
            break
    model.fit_history(x_tr, y_tr)
    return {"final": {k: history[k][-1] for k in evals}, "best": None, "history": history, "seconds": time.time() - t0}
