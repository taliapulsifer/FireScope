from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LAYER_URL = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0"
QUERY_URL = f"{LAYER_URL}/query"

WHERE = "state = 'CA' AND fire_year BETWEEN 2015 AND 2024"

FIELDS = [
    "objectid",
    "fod_id",
    "fire_year",
    "discovery_date",
    "latitude",
    "longitude",
]

BATCH_SIZE = 200
MAX_WORKERS = 4

def query_fire_history(params):
    retries = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    with requests.Session() as session:
        session.mount(
            "https://",
            HTTPAdapter(max_retries=retries),
        )

        response = session.get(
            QUERY_URL,
            params={"f": "json", **params},
            timeout=(10, 90),
        )
        response.raise_for_status()
        payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"ArcGIS query failed: {payload['error']}")

    return payload


def fetch_batch(object_ids):
    payload = query_fire_history({
        "objectIds": ",".join(map(str, object_ids)),
        "outFields": ",".join(FIELDS),
        "returnGeometry": "false",
    })

    if payload.get("exceededTransferLimit"):
        raise RuntimeError("Batch was truncated; reduce BATCH_SIZE.")

    rows = [
        feature["attributes"]
        for feature in payload["features"]
    ]

    received_ids = [row["objectid"] for row in rows]

    if (
        len(received_ids) != len(object_ids)
        or set(received_ids) != set(object_ids)
    ):
        raise RuntimeError("Batch contains missing or duplicate records.")

    return rows


def download_fire_history(max_workers=MAX_WORKERS):
    if max_workers < 1:
        raise ValueError("max_workers must be at least 1.")

    payload = query_fire_history({
        "where": WHERE,
        "returnIdsOnly": "true",
    })

    object_ids = sorted(payload["objectIds"] or [])

    if not object_ids:
        raise RuntimeError("No matching records; check the source and filter.")

    batches = [
        object_ids[start:start + BATCH_SIZE]
        for start in range(0, len(object_ids), BATCH_SIZE)
    ]

    rows = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_batch, batch)
            for batch in batches
        ]

        for completed, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            print(f"Downloaded {completed}/{len(batches)} batches")

    frame = pd.DataFrame(rows)

    if (
        len(frame) != len(object_ids)
        or frame["objectid"].duplicated().any()
    ):
        raise RuntimeError("Combined download failed validation.")

    return frame.sort_values("objectid").reset_index(drop=True)


if __name__ == "__main__":
    from time import perf_counter

    RUN_FULL_DOWNLOAD = False
    FULL_DOWNLOAD_WORKERS = 4

    total_started = perf_counter()

    # ------------------------------------------------------------
    # 1. Retrieve IDs for California fires from 2015–2024.
    # ------------------------------------------------------------
    started = perf_counter()

    payload = query_fire_history({
        "where": WHERE,
        "returnIdsOnly": "true",
    })
    object_ids = sorted(payload["objectIds"] or [])

    ids_seconds = perf_counter() - started

    if not object_ids:
        raise RuntimeError("No matching fire records found.")

    assert len(object_ids) == len(set(object_ids)), "Duplicate source IDs"

    print(f"Found {len(object_ids):,} matching fire records")

    # ------------------------------------------------------------
    # 2. Download five records.
    # ------------------------------------------------------------
    sample_ids = object_ids[:5]
    started = perf_counter()

    sample_rows = fetch_batch(sample_ids)

    sample_download_seconds = perf_counter() - started

    # ------------------------------------------------------------
    # 3. Create the sample DataFrame.
    # ------------------------------------------------------------
    started = perf_counter()

    sample = pd.DataFrame(sample_rows)

    dataframe_seconds = perf_counter() - started

    # ------------------------------------------------------------
    # 4. Validate the sample.
    # ------------------------------------------------------------
    started = perf_counter()

    assert set(FIELDS).issubset(sample.columns), "Missing columns"
    assert len(sample) == len(sample_ids), "Incorrect record count"
    assert sample["objectid"].is_unique, "Duplicate records"
    assert set(sample["objectid"]) == set(sample_ids), "Incorrect IDs"
    assert sample["fire_year"].between(2015, 2024).all(), "Unexpected year"
    assert sample["discovery_date"].notna().all(), "Missing discovery dates"
    assert sample["latitude"].between(-90, 90).all(), "Invalid latitude"
    assert sample["longitude"].between(-180, 180).all(), "Invalid longitude"

    validation_seconds = perf_counter() - started
    sample_total_seconds = perf_counter() - total_started

    print("\nSample records:")
    print(sample.to_string(index=False))

    print("\nSample test timing:")
    print(f"  ID lookup and sorting: {ids_seconds:.3f} s")
    print(f"  Sample download:       {sample_download_seconds:.3f} s")
    print(f"  DataFrame creation:    {dataframe_seconds:.6f} s")
    print(f"  Validation:            {validation_seconds:.6f} s")
    print(f"  Total:                 {sample_total_seconds:.3f} s")
    print("\nSmall download test passed.")

    # ------------------------------------------------------------
    # 5. Check that invalid worker counts are rejected.
    #    These calls should fail before making network requests.
    # ------------------------------------------------------------
    for invalid_workers in (0, -1):
        try:
            download_fire_history(max_workers=invalid_workers)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Worker count {invalid_workers} should have been rejected."
            )

    print("Invalid worker count tests passed.")

    # ------------------------------------------------------------
    # 6. Benchmark concurrent downloads on the same 2,000 IDs.
    #    Each configuration downloads the sample again.
    # ------------------------------------------------------------
    benchmark_ids = object_ids[:2_000]

    batches = [
        benchmark_ids[start:start + BATCH_SIZE]
        for start in range(0, len(benchmark_ids), BATCH_SIZE)
    ]

    print(
        f"\nConcurrency benchmark: "
        f"{len(benchmark_ids):,} records across {len(batches)} batches"
    )

    results = []
    baseline_seconds = None
    reference_frame = None

    for workers in (1, 2, 4, 8):
        started = perf_counter()
        benchmark_rows = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(fetch_batch, batch)
                for batch in batches
            ]

            for future in as_completed(futures):
                benchmark_rows.extend(future.result())

        # Stop timing before validation and printing.
        elapsed = perf_counter() - started

        benchmark_frame = (
            pd.DataFrame(benchmark_rows)
            .sort_values("objectid")
            .reset_index(drop=True)
        )

        assert len(benchmark_frame) == len(benchmark_ids), (
            f"{workers} workers: incorrect record count"
        )
        assert benchmark_frame["objectid"].is_unique, (
            f"{workers} workers: duplicate records"
        )
        assert set(benchmark_frame["objectid"]) == set(benchmark_ids), (
            f"{workers} workers: incorrect IDs"
        )
        assert benchmark_frame["fire_year"].between(2015, 2024).all(), (
            f"{workers} workers: unexpected year"
        )

        # Ensure concurrency did not change the returned data.
        if reference_frame is None:
            reference_frame = benchmark_frame
        else:
            pd.testing.assert_frame_equal(
                reference_frame,
                benchmark_frame,
                check_like=True,
            )

        if baseline_seconds is None:
            baseline_seconds = elapsed

        speedup = baseline_seconds / elapsed
        records_per_second = len(benchmark_frame) / elapsed

        results.append({
            "workers": workers,
            "seconds": elapsed,
            "records_per_second": records_per_second,
            "speedup": speedup,
        })

        print(
            f"  {workers} workers: {elapsed:.3f} s | "
            f"{records_per_second:,.0f} records/s | "
            f"{speedup:.2f}x speedup"
        )

    fastest = min(results, key=lambda result: result["seconds"])

    print("\nAll concurrency checks passed.")
    print(f"Fastest in this run: {fastest['workers']} workers")
    print("Network conditions and server caching can affect these results.")

    # ------------------------------------------------------------
    # 7. Optional: download and validate the complete dataset.
    # ------------------------------------------------------------
    if RUN_FULL_DOWNLOAD:
        print(
            f"\nStarting full download with "
            f"{FULL_DOWNLOAD_WORKERS} workers..."
        )
        started = perf_counter()

        fires = download_fire_history(
            max_workers=FULL_DOWNLOAD_WORKERS
        )

        full_download_seconds = perf_counter() - started

        assert not fires.empty, "Full dataset is empty"
        assert fires["objectid"].is_unique, "Duplicate records"
        assert len(fires) == len(object_ids), "Incorrect total record count"
        assert set(fires["objectid"]) == set(object_ids), (
            "Downloaded IDs differ from the initial source query"
        )
        assert fires["fire_year"].between(2015, 2024).all(), (
            "Unexpected year"
        )
        assert fires["discovery_date"].notna().all(), (
            "Missing discovery dates"
        )
        assert fires["latitude"].between(-90, 90).all(), (
            "Invalid latitude"
        )
        assert fires["longitude"].between(-180, 180).all(), (
            "Invalid longitude"
        )

        print(
            f"\nDownloaded {len(fires):,} records "
            f"in {full_download_seconds:.2f} seconds"
        )
        print("\nRecords per year:")
        print(fires.groupby("fire_year").size())

        print("\nMissing values:")
        print(fires.isna().sum())

        print("\nFull download test passed.")
    else:
        print("\nFull download skipped.")
        print("Set RUN_FULL_DOWNLOAD = True to enable it.")

    print(
        f"\nEntire test run finished in "
        f"{perf_counter() - total_started:.2f} seconds."
    )
