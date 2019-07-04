This is a MLsploit module for using [Barnum](https://github.com/carter-yagemann/barnum-learner).

## Installation

See MLsploit's documentation for how to [import a module](https://github.com/mlsploit/mlsploit-rest-api/blob/master/README.md):

    python manage.py createmodule barnum https://github.com/carter-yagemann/barnum-mlsploit.git

## Usage

This module contains three functions.

### Mimicus

This function takes PDF files and modifies them using [Mimicus](https://github.com/srndic/mimicus), which is a system
designed to evade static PDF malware classifiers.

To use this module, upload your PDF files via the MLsploit web UI and pass them to a pipeline containing the Mimicus function.
The PDF files will be overwritten with their modified versions.

### Barnum-Train

This function takes traces produced using [Barnum's Tracer](https://github.com/carter-yagemann/barnum-tracer) and trains
on them using [Barnum's Learner](https://github.com/carter-yagemann/barnum-learner). At a very high level, Barnum is a
system that detects document malware by analyzing control flow traces for anomalous behavior.

To upload a trace into MLsploit, you must perform the following steps:

1. Capture a trace using Barnum Tracer.

2. Preprocess the trace using `preprocess.py`, which is provided by Barnum Learner (see the
[README](https://github.com/carter-yagemann/barnum-learner/blob/master/README.md)).

3. Zip each trace directory, one per sample.

Here's an example of what one trace ZIP should look like:

```
$ unzip -l trace-a.zip
Archive:  trace-a.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2019-01-03 16:56   44a7851c6f204ed156203b178f1d59a7c0e02b26a447fef7be648c5366aa4312/
  1177960  2019-01-03 16:55   44a7851c6f204ed156203b178f1d59a7c0e02b26a447fef7be648c5366aa4312/trace_parsed.gz
      861  2019-01-03 16:53   44a7851c6f204ed156203b178f1d59a7c0e02b26a447fef7be648c5366aa4312/mapping.txt.gz
       85  2019-01-03 16:53   44a7851c6f204ed156203b178f1d59a7c0e02b26a447fef7be648c5366aa4312/info.txt
---------                     -------
  1178906                     4 files
```

It is okay if your trace contains additional files not shown above, but it must contain a `trace_parsed.gz` and `info.txt` at
a minimum.

Once your traces are uploaded via the MLsploit web UI, create a pipeline containing this function and pass
it traces.

This function will produce the file `model.zip`, which contains the trained model.

### Barnum-Eval

This function takes an already trained model and evaluates it on a set of traces.

It works similarly to the Barnum-Train function, except it should be passed a `model.zip` along with the traces.
Currently, the model file *must* be named `model.zip` and *must* contain the files `lstm.h5`, `lstm.json` and
`svm`.

For users that want to train a model outside of MLsploit (without using the Barnum-Train function) and upload
it, here's an example of what a `model.zip` should look like:

```
$ unzip -l model.zip
Archive:  model.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
   996720  2019-07-03 17:02   lstm.h5
     4989  2019-07-03 17:02   lstm.json
    24229  2019-07-03 17:40   svm
---------                     -------
  1025938                     3 files
```

## Testing

To test whether this module is correctly installed into MLsploit, test
input files are provided in the `examples` directory. Upload its
contents via the MLsploit web UI.

Note, this data is only for verifying that the module works. Do not expect the
provided model to yield high accuracy.
