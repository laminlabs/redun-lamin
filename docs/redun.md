---
execute_via: python
---

# Redun

Here, we'll see how to track redun workflow runs with LaminDB.

```{note}

This use case is based on [github.com/ricomnl/bioinformatics-pipeline-tutorial](https://github.com/ricomnl/bioinformatics-pipeline-tutorial/tree/redun).

```

## Amend the workflow

Here is how to instrument a `redun` workflow for tracking with `lamindb`:

1. Add `ln.track()` ([see on GitHub](https://github.com/laminlabs/redun-lamin-fasta/blob/main/docs/workflow.py#L45))

2. Register desired output files or folders by creating artifacts for them ([see on GitHub](https://github.com/laminlabs/redun-lamin-fasta/blob/main/redun_lamin_fasta/lib.py#L315)):

   ```python
   ln.Artifact(output_path, key="data/results.tar.gz").save()
   ```

3. Add a `finish()` task that calls `ln.finish()` ([see on GitHub](https://github.com/laminlabs/redun-lamin-fasta/blob/main/docs/workflow.py#L30))

4. Optionally cache/stage input files ([see on GitHub](https://github.com/laminlabs/redun-lamin-fasta/blob/main/docs/workflow.py#L41))

<!-- #region -->

:::{dropdown} Why not use `@ln.flow()` for `main()`?

Because `main()` in redun is typically a scheduler/executor task rather than a task that performs the actual computation. `ln.flow()` would hence measure the execution time of scheduling not an actual compute run.

If one wanted to use `@ln.flow()` it's advisable to wrap the scheduler:

```python
@ln.flow()
def run_pipeline(...):
    scheduler = Scheduler()
    result = scheduler.run(main(...))  # run the main task
    ln.Artifact(result.path, key="data/results.tgz").save()
    return result
```

:::

<!-- #endregion -->

## Run redun

Let's see what the input files are:

```python
!ls ./fasta
```

Create a lamindb test instance:

```python
# pip install lamindb redun git+http://github.com/laminlabs/redun-lamin-fasta
!lamin init --storage ./test-redun-lamin
```

Register each input file individually as an artifact:

```python
import lamindb as ln
import json

ln.Artifact.from_dir("./fasta").save()
```

Run the redun workflow:

```python
!redun run workflow.py main --input-dir ./fasta --tag run=test-run  1> run_logs.txt 2>run_logs.txt
```

Inspect the logs:

```python
!cat run_logs.txt
```

View data lineage:

```python
artifact = ln.Artifact.get(key="data/results.tgz")
artifact.view_lineage()
```

```python
artifact.transform.describe()
```

```python
artifact.run.describe()
```

## View transforms and runs in LaminHub

Explore it at [lamin.ai/laminlabs/lamindata/transform/taasWKawCiNA](https://lamin.ai/laminlabs/lamindata/transform/taasWKawCiNA).

<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/xzIfn0p1wAqXH1TZ0001.png" width="900px">

## View the database content

```python
ln.view()
```

## Appendix

### Map the redun execution id

If we want to be able to query LaminDB for redun execution ID, this here is a way to get it:

```python
# export the run information from redun
!redun log --exec --exec-tag run=test-run --format json --no-pager > redun_exec.json
# load the redun execution id from the JSON and store it in the LaminDB run record
with open("redun_exec.json") as file:
    redun_exec = json.loads(file.readline())
artifact.run.reference = redun_exec["id"]
artifact.run.reference_type = "redun_id"
artifact.run.save()
```

### Map the redun run report

While `lamindb` auto-tracks the logs of the main python process you might also want to link the dedicated redun logs:

```python
report = ln.Artifact(
    "run_logs.txt",
    description=f"Redun run report of {redun_exec['id']}",
    run=False,
    kind="__lamindb_run__",  # mark as auxiliary artifact for the run
).save()
artifact.run.report = report
artifact.run.save()
```

Delete the test instance:

```python
!rm -rf test-redun-lamin
!lamin delete --force test-redun-lamin
```
