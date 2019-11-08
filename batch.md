# Globus CLI Batch Transfer Recipe

In this example we're going to submit transfers from two directories on a single Globus endpoint and have the data copied a single common directory. This can be used to aggregate results from different simulations or other jobs. It will show how to do a lot of things with the Globus CLI along the way. This example can be useful if you deal with hundreds or thousands of files and directories at a single time.

We'll walkthrough of how to use the [Globus CLI](https://docs.globus.org/cli/) to list, filter, and [batch submit a transfer](https://docs.globus.org/cli/reference/transfer/) from two locations into a single destination folder. To get started, you'll need to the have the Globus CLI installed and be logged in. See the [getting started](README.md#getting-started) section of the README.

## Get the Endpoint UUIDs

We're going to copy data from ALCF's [Theta](https://www.alcf.anl.gov/theta) to [Petrel](http://petrel.alcf.anl.gov/), the storage system used to support community data repositories. Globus makes heavy use of UUIDs to refer to things like endpoints, so we'll search for them.

```
$ globus endpoint search theta
ID                                   | Owner             | Display Name  
------------------------------------ | ----------------- | --------------
08925f04-569f-11e7-bef8-22000b9a448b | alcf@globusid.org | alcf#dtn_theta
$ globus endpoint search petrel#e3sm
ID                                   | Owner               | Display Name
------------------------------------ | ------------------- | ------------
dabdceba-6d04-11e5-ba46-22000b92c6ec | petrel@globusid.org | petrel#e3sm 
```

##  Set Environment Variables to Track Things

Memorizing UUIDs is not a recommended practice. We'll set environment variables to track them.

```
$ theta_ep=08925f04-569f-11e7-bef8-22000b9a448b
$ petrel_e3sm_ep=dabdceba-6d04-11e5-ba46-22000b92c6ec
```

While we're at it, we'll set our source and destination directories to prevent typos and errors.

```
$ run1_path=/lus/theta-fs0/projects/example/run1/
$ run2_path=/lus/theta-fs0/projects/example/run1/
$ e3sm_path=/users/rick/watertable/
```

## Check Endpoint Activation

If the endpoint isn't [activated](https://docs.globus.org/api/transfer/endpoint_activation/#web_activation), go to the [Globus web app](https://app.globus.org/), search for the endpoint by name or UUID and you'll be prompted for credentials to activate it. The destination in this example is a shared endpoint which will be [auto-activated](https://docs.globus.org/api/transfer/endpoint_activation/#auto_activation) by the Globus CLI.

```
$ globus endpoint is-activated $theta_ep 
08925f04-569f-11e7-bef8-22000b9a448b is activated
Exit: 0
$ globus endpoint is-activated $petrel_e3sm_ep 
dabdceba-6d04-11e5-ba46-22000b92c6ec does not require activation
Exit: 0
```

## List Source Files

The `globus ls` works a lot like `ls` on a POSIX command line and we can use the `--filter` option to save us from parsing the full list.

```
$ globus ls --filter '~*watertable.h0*' $theta_ep:$run1_path > run1_watertable_files.txt 
$ globus ls --filter '~*watertable.h0*' $theta_ep:$run2_path > run2_watertable_files.txt
```

The batch transfer expects a list of source files and their corresponding destination filenames. In this case, those are the same and our files will have lines like:
`<sourcefile name> <source filename>`. (If we wanted to move the entire directory this would be a bit easier, we would use a recursive transfer. But we want to only move _some_ of the files from the source directories.)

```
$ for i in `cat run1_watertable_files.txt `
  do
      echo "$i $i"
  done > run1_watertable_files_src_dest.txt
$ for i in `cat run2_watertable_files.txt `
  do
      echo "$i $i"
  done > run2_watertable_files_src_dest.txt
```

## Batch Submit the Transfers

The base Globus CLI transfer command is

```
$ globus transfer <source ep UUID>:<source path> <destination ep UUID>:<destination path>
```

The `--batch` option to the transfer command will read the `stdin` input from the file line by line to build the transfer request. The source and destination paths from the input files are relative to the paths we specify using `<source endpoint UUID>:<source path>` and `<destination endpoint UUID>:<destination path>`.

You could submit one transfer per file, but then you would have a lot of tasks to monitor and the underlying Globus Connect servers would not be able efficiently aggregate the files. In other words, that's too much work and would be slower.

```
$ globus transfer --batch $theta_ep:$run1_path $petrel_e3sm_ep:$e3sm_path < run1_watertable_files_src_dest.txt 
Message: The transfer has been accepted and a task has been created and queued for execution
Task ID: 1d499566-01ab-11ea-be94-02fcc9cdd752
$ globus transfer --batch $theta_ep:$run2_path $petrel_e3sm_ep:$e3sm_path < run2_watertable_files_src_dest.txt 
Message: The transfer has been accepted and a task has been created and queued for execution
Task ID: 15173a2e-01ab-11ea-be94-02fcc9cdd752
```

## Check Status on the Transfers

You can monitor the tasks using the [web app](https://app.globus.org/activity) or with the CLI. Here, I've waited long enough for them to have finished. Since this example was within Argonne for a few hundreds of gigabytes, that's not surprising. Your transfer rates may vary.

### `run1` Transfer

```
$ globus task show 1d499566-01ab-11ea-be94-02fcc9cdd752
Label:                   None
Task ID:                 1d499566-01ab-11ea-be94-02fcc9cdd752
Is Paused:               False
Type:                    TRANSFER
Directories:             0
Files:                   121
Status:                  SUCCEEDED
Request Time:            2019-11-07 22:08:24+00:00
Faults:                  0
Total Subtasks:          242
Subtasks Succeeded:      242
Subtasks Pending:        0
Subtasks Retrying:       0
Subtasks Failed:         0
Subtasks Canceled:       0
Subtasks Expired:        0
Completion Time:         2019-11-07 22:09:57+00:00
Source Endpoint:         alcf#dtn_theta
Source Endpoint ID:      08925f04-569f-11e7-bef8-22000b9a448b
Destination Endpoint:    petrel#e3sm
Destination Endpoint ID: dabdceba-6d04-11e5-ba46-22000b92c6ec
Bytes Transferred:       44631218808
Bytes Per Second:        480727214
```

### `run2` Transfer

```
$ globus task show 15173a2e-01ab-11ea-be94-02fcc9cdd752
Label:                   None
Task ID:                 15173a2e-01ab-11ea-be94-02fcc9cdd752
Is Paused:               False
Type:                    TRANSFER
Directories:             0
Files:                   481
Status:                  SUCCEEDED
Request Time:            2019-11-07 22:08:11+00:00
Faults:                  0
Total Subtasks:          962
Subtasks Succeeded:      962
Subtasks Pending:        0
Subtasks Retrying:       0
Subtasks Failed:         0
Subtasks Canceled:       0
Subtasks Expired:        0
Completion Time:         2019-11-07 22:11:27+00:00
Source Endpoint:         alcf#dtn_theta
Source Endpoint ID:      08925f04-569f-11e7-bef8-22000b9a448b
Destination Endpoint:    petrel#e3sm
Destination Endpoint ID: dabdceba-6d04-11e5-ba46-22000b92c6ec
Bytes Transferred:       177418316088
Bytes Per Second:        901833634
```

## List the New Files

As a quality check on my file lists, etc., I will list the number of files that are now on the common destination to the number of source files.

```
$ globus ls $petrel_e3sm_ep:$e3sm_path > petrel_files.txt
$ wc petrel_files.txt 
     601     601   54070 petrel_files.txt
$ wc run2_watertable_files.txt run1_watertable_files.txt 
     481     481   43270 run2_watertable_files.txt
     121     121   10890 run1_watertable_files.txt
     602     602   54160 total
```

Hmmm. Off by one...turns out there was a common file in both directories. It's worth checking for collisions like that when you copy different things to the same destination. That's not just for Globus. The POSIX command line can also be unforgiving. Remember: _Windows has a trash can, POSIX has an incinerator._

## Cleaning Up

Speaking of incinerators, as you copy data around, sometimes it's just to stage data for another section of the pipeline, which was this case. After the consolidated data was processed and moved to its next location, we should remove the intermediate directory.

*BE AWARE* when using `globus delete`, especially `globus delete -r`. It's just like being on the command line; if you have write permissions to the target of that command, it's going away. I'm considering a pull request for the Globus CLI to have a software Easter egg where `incinerate` is a valid alias for `delete`.

```
$ globus delete -r $petrel_e3sm_ep:$e3sm_path 
Message: The delete has been accepted and a task has been created and queued for execution
Task ID: 30762c84-01c0-11ea-8a5e-0e35e66293c2
```
