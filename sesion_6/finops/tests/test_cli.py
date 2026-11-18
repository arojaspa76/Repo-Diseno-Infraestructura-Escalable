from finops_sim.cli import main


def test_cli_scenario_runs(capsys):
    assert main(["scenario", "--instance", "gpu-s"]) == 0
    out = capsys.readouterr().out
    assert "ILUSTRATIVOS" in out and "commit_baseline" in out and "API administrada" in out


def test_cli_rightsize_runs(capsys):
    assert main(["rightsize", "--instance", "gpu-m", "--csv", "data/utilizacion_ejemplo.csv"]) == 0
    assert "Ahorro mensual" in capsys.readouterr().out


def test_cli_bad_instance_returns_error_code(capsys):
    assert main(["capacity", "--instance", "no-existe"]) == 2
    assert "no existe" in capsys.readouterr().err
