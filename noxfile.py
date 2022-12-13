import nox
from lndb_setup.test.nox import build_docs, run_pre_commit, run_pytest

nox.options.reuse_existing_virtualenvs = True


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"])
def build(session):
    session.install(".[dev,test]")
    run_pytest(session)
    build_docs(session)
