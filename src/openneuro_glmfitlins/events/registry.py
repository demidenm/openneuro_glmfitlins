"""Registry of per-dataset event-fix functions.

Each dataset module in ``events/datasets/`` registers one function::

    @register_events("ds001357")
    def ds001357(events_df, task, ctx):
        ...
        return modified_df  # or None when nothing needs to change

The contract is ``fn(events_df: DataFrame, task: str, ctx: EventsContext) -> DataFrame | None``.
Functions must not write the events file themselves; the caller decides whether to write
by comparing the returned table with the file on disk (see ``events.prep.apply_events_fix``).
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable, Dict

EventsFixer = Callable[..., object]

_REGISTRY: Dict[str, EventsFixer] = {}
_LOADED = False


def register_events(study_id: str) -> Callable[[EventsFixer], EventsFixer]:
    """Decorator that registers ``fn`` as the event fix for ``study_id``."""

    def decorator(fn: EventsFixer) -> EventsFixer:
        if study_id in _REGISTRY and _REGISTRY[study_id] is not fn:
            raise ValueError(f"Event fix for {study_id} is registered twice "
                             f"({_REGISTRY[study_id].__module__} and {fn.__module__})")
        _REGISTRY[study_id] = fn
        return fn

    return decorator


def _load_all() -> None:
    global _LOADED
    if _LOADED:
        return
    from . import datasets

    for mod in pkgutil.iter_modules(datasets.__path__):
        importlib.import_module(f"{datasets.__name__}.{mod.name}")
    _LOADED = True


def get_events_fixer(study_id: str) -> EventsFixer:
    """Return the registered fix for ``study_id``; raise LookupError if there is none."""
    _load_all()
    try:
        return _REGISTRY[study_id]
    except KeyError:
        raise LookupError(
            f"No event fix registered for {study_id}. Add "
            f"src/openneuro_glmfitlins/events/datasets/{study_id}.py with "
            f'@register_events("{study_id}").'
        ) from None


def registered_studies() -> list[str]:
    _load_all()
    return sorted(_REGISTRY)
