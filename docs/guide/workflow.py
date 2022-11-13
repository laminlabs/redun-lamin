"""workflow.py"""
# This code is a copy from https://github.com/ricomnl/bioinformatics-pipeline-tutorial/blob/2ccfe727f56b449e28e83fee2d9f003ec44a2cdf/wf/workflow.py  # noqa
# Copyright Rico Meinl 2022
from enum import Enum
from typing import List

from redun import File, task
from redun.file import glob_file

from redun_lamin_fasta.lib import (
    archive_results_task,
    count_amino_acids_task,
    digest_protein_task,
    get_report_task,
    plot_count_task,
)

redun_namespace = "redun_lamin_fasta.workflow"


class Executor(Enum):
    default = "default"
    process = "process"
    batch = "batch"
    batch_debug = "batch_debug"


@task(version="0.0.1", config_args=["executor"])
def main(
    input_dir: str,
    amino_acid: str = "C",
    enzyme_regex: str = "[KR]",
    missed_cleavages: int = 0,
    min_length: int = 4,
    max_length: int = 75,
    executor: Executor = Executor.default,
) -> List[File]:
    input_fastas = [File(f) for f in glob_file(f"{input_dir}/*.fasta")]
    task_options = dict(executor=executor.value)
    peptide_files = [
        digest_protein_task.options(**task_options)(
            fasta,
            enzyme_regex=enzyme_regex,
            missed_cleavages=missed_cleavages,
            min_length=min_length,
            max_length=max_length,
        )
        for fasta in input_fastas
    ]
    aa_count_files = [
        count_amino_acids_task.options(**task_options)(
            fasta, peptides, amino_acid=amino_acid
        )
        for (fasta, peptides) in zip(input_fastas, peptide_files)
    ]
    count_plots = [
        plot_count_task.options(**task_options)(aa_count) for aa_count in aa_count_files
    ]
    report_file = get_report_task.options(**task_options)(aa_count_files)
    results_archive = archive_results_task.options(**task_options)(
        count_plots, report_file
    )
    # LaminDB is called at the end, once all tasks have successfully completed
    from pathlib import Path

    import lamindb as ln
    import lamindb.schema as lns
    import lndb_setup
    from lamin_logger import logger

    lndb_setup.load("redun-lamin-fasta")  # load the LaminDB instance we'd like to use
    pipeline = ln.select(lns.Pipeline, name="lamin-redun-fasta").one()
    run = lns.Run(name="Test run", pipeline_id=pipeline.id, pipeline_v=pipeline.v)
    logger.info(f"Loaded pipeline {pipeline}")
    logger.info(f"Created run {run}")
    # Ingest pipeline outputs
    ingest = ln.Ingest(run)
    for filepath in Path("./data/").glob(
        "results.tgz"
    ):  # User needs to decide what to track, here just results.tgz  # noqa
        ingest.add(filepath)
    ingest.commit()
    # Link pipeline inputs
    inputs = (
        ln.select(lns.DObject).join(lns.Run).join(lns.Jupynb, id="0ymQDuqM5Lwq").all()
    )
    links = [lns.RunIn(dobject_id=dobject.id, run_id=run.id) for dobject in inputs]
    ln.add(links)
    return results_archive
