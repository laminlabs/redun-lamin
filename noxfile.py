import nox
from laminci import convert_executable_md_files, upload_docs_artifact
from laminci.nox import (
    build_docs,
    install_lamindb,
    login_testuser1,
    run_pre_commit,
    run_pytest,
)

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
def install(session: nox.Session):
    session.run(*"uv pip install --system .[dev]".split())
    install_lamindb(session, branch="main", extras="bionty")


@nox.session
def build(session):
    convert_executable_md_files()
    login_testuser1(session)
    run_pytest(session, coverage=False)
    build_docs(session)
    upload_docs_artifact()
