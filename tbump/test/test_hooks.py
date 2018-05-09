import tbump.hooks
import tbump.main


def test_run_hooks(test_repo, mock):
    mock_run = mock.patch("subprocess.run")
    hook_runner = tbump.hooks.HooksRunner()
    hook_runner.add_hook("fake-yarn", "python yarn.py {new_version}")

    hook_runner.run(new_version="1.2.41-alpha-2")

    mock_run.assert_called_with("python yarn.py 1.2.41-alpha-2", shell=True, cwd=None)
