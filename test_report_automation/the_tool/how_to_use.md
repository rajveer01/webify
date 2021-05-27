># **How to Guide**

> Call [report_automation.py](report_automation.py) file with proper parameters
> ***
> Note: CurrentDirectory Should be Webify Directory



| Parameters              | Purpose                                                          | Example                                                                                                                              |
| ----------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1.app_name              | App name                                                         | IAD                                                                                                                                  |
| 2.tool_dir              | tool directory to change CW directory after setting the Loggers  | test_report_automation\the_tool                                                                                                      |
| 3. rel_run_logs_folder  | Relative to tools directory for run logs After Changed directory | ...\the_tool\\ _```Artifacts\Feb Release 2020\REM\REM - Feb Release 2020 - Load Run 24 - Oct 12, 2020 at 10-12-39 PM - Run Logs```_  |
| 4. rel_artifacts_folder | Relative to the tools directory for collecting artifacts         | ...\the_tool\\_```Artifacts\Feb Release 2020\REM\REM - Feb Release 2020 - Load Run 24 - Oct 12, 2020 at 10-12-39 PM -  Artifacts```_ |
| 5. stdlog_file_name     | log file name for logs                                           | REM - Run 24 - Oct 12, 2020 at 10-12-39 PM - STD Log.log                                                                             |
| 6. stdout_file_name     | output file name to log std output                               | REM - Run 24 - Oct 12, 2020 at 10-12-39 PM - STD Out.log                                                                             |
| 7. stderr_file_name     | error file name to log std errors                                | REM - Run 24 - Oct 12, 2020 at 10-12-39 PM - STD ERR.log                                                                             |


```java

a = [1, 3, 5, 6]
b = [4, 5, 2, 5]

inp = input('Choose array')

if (inp == 'a')
    for (e in a)
        print('current Element is: ' + e)
        e = e * 10

else if (inp == 'b')
    for (e in b)
        print('current Element is: ' + e)
        e = e + 5

// Output
// for input 'a' -> 1 3 5 6
// for input 'b' -> 4 5 2 5


```

