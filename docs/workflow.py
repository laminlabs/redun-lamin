"""workflow.py."""

# This code is based on a copy from https://github.com/ricomnl/bioinformatics-pipeline-tutorial/blob/2ccfe727f56b449e28e83fee2d9f003ec44a2cdf/wf/workflow.py
# Copyright Rico Meinl 2022
from enum import Enum

import lamindb as ln
from redun import File, task

import redun_lamin_fasta
from redun_lamin_fasta.lib import (
    archive_results_task,
    count_amino_acids_task,
    digest_protein_task,
    get_report_task,
    plot_count_task,
)

redun_namespace = redun_lamin_fasta.__name__


class Executor(str, Enum):
    default = "default"
    process = "process"
    batch = "batch"
    batch_debug = "batch_debug"


@task(version="0.0.1", config_args=["executor"])
@ln.flow()
def main(
    input_dir: str,
    amino_acid: str = "C",
    enzyme_regex: str = "[KR]",
    missed_cleavages: int = 0,
    min_length: int = 4,
    max_length: int = 75,
    executor: Executor = Executor.default,
) -> list[File]:
    # filter input files
    input_filepaths = [
        artifact.cache()
        for artifact in ln.Artifact.filter(key__startswith=input_dir.lstrip("./"))
    ]
    # (optional) annotate the fasta files by Protein
    # import bionty as bt
    # for input_file in ln.Artifact.filter(key__startswith="fasta/").all():
    #     input_filepath = input_file.cache()
    #     with open(input_filepath) as f:
    #         header = f.readline()
    #         uniprotkb_id = header.split("|")[1]
    #         name = header.split("|")[2].split(" OS=")[0]
    #     protein = bt.Protein.from_source(uniprotkb_id=uniprotkb_id, organism="human")
    #     protein.name = name
    #     protein.save()
    #     input_file.proteins.add(protein)

    # execute redun tasks
    task_options = {"executor": executor.value}
    input_fastas = [File(str(path)) for path in input_filepaths]
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
    return results_archive
