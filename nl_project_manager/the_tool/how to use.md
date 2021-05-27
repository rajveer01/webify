># **How to Guide**

> Call [workflow.py](workflow.py) file with proper parameters
> ***
> Note: CurrentDirectory Should be Webify Directory



| Parameters             | Purpose                                                          | Example                                                            |
| ---------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1. app_name            | App name                                                         | IAD                                                                |
| 2. tool_dir            | tool directory to change CW directory after setting the Loggers  | neoload_project_manager\the_tool                                   |
| 3. rel_run_logs_folder | Relative to tools directory for run logs After Changed directory | ...\the_tool\ _```json_dicts\REM - Oct 12, 2020 at 10-12-39 PM```_ |
| 4. json_file_name      | Json File Name under run logs folder                             | ...\ _```REM - Oct 12, 2020 at 10-12-39 PM.json```_                |
| 5. log_file_name       | log file name for logs                                           | REM - Oct 12, 2020 at 10-12-39 PM - STD Log.log                    |
| 6. stdout_file         | output file name to log std output                               | REM - Oct 12, 2020 at 10-12-39 PM - STD Out.log                    |
| 7. stderr_file         | error file name to log std errors                                | REM - Oct 12, 2020 at 10-12-39 PM - STD ERR.log                    |

