from __future__ import annotations

import json

from book_translator.models.job import JobMeta


def test_create_run_returns_12_char_id(store):
    run_id = store.create_run(JobMeta(model="m", params={}))
    assert len(run_id) == 12
    assert run_id.isalnum()


def test_create_run_makes_src_dst_dirs(store):
    run_id = store.create_run(JobMeta(model="m", params={}))
    assert store.src_dir(run_id).is_dir()
    assert store.dst_dir(run_id).is_dir()


def test_read_meta_roundtrip(store):
    run_id = store.create_run(JobMeta(model="m", params={"t": 0.5}))
    meta = store.read_meta(run_id)
    assert meta.model == "m"
    assert meta.params == {"t": 0.5}


def test_meta_json_contains_only_model_and_params(store):
    run_id = store.create_run(JobMeta(model="m", params={}))
    data = json.loads((store.run_dir(run_id) / "meta.json").read_text("utf-8"))
    assert set(data.keys()) == {"model", "params"}


def test_update_meta(store):
    run_id = store.create_run(JobMeta(model="m1", params={}))
    store.update_meta(run_id, JobMeta(model="m2", params={}))
    meta = store.read_meta(run_id)
    assert meta.model == "m2"


def test_list_runs_returns_all_created(store):
    ids = [store.create_run(JobMeta(model="m", params={})) for _ in range(3)]
    runs = store.list_runs()
    assert len(runs) == 3
    for run_id in ids:
        assert run_id in runs


def test_list_runs_sorted(store):
    store.create_run(JobMeta(model="m", params={}))
    store.create_run(JobMeta(model="m", params={}))
    runs = store.list_runs()
    assert runs == sorted(runs)


def test_meta_json_atomic_write(store):
    run_id = store.create_run(JobMeta(model="m", params={}))
    assert (store.run_dir(run_id) / "meta.json.tmp").exists() is False
