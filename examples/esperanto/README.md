# Running

0. Navigate to `fairseq/examples/esperanto`
1. Find the directory of all your data. I put the split train/test/validation stuff in `data/esperanto_tokenizer` and `data/generic_tokenizer`. they are the same split, and are pre-tokenized.
    - these are just named `(train|valid|test).(en|eo)`
2. Update the paths in `train_semantic.sh` and `train_generic.sh`
    - that is, update `TEXT=/home/marco/github/EsperantoTokenization/data/esperanto_tokenizer` to wherever your semantic tokenizer data is
3. Set a seed (just update `SEED=0`)
4. Run `sh train_generic.sh` or `sh train_semantic.sh`
    - you can test that things work by adding the line `--max-epoch 3 \` in the `fairseq-train` options in these bash scripts
5. When you run it, check `fairseq/experiment_outputs` and you will be able to see a folder with your experiment name (something like `generic_tokenizer_{SEED}`)
    - the logs will show you how well it is training
6. When training finishes (the last line of the log will say `training done in XYZ seconds`), a new `BLEU.log` file will pop up. At the bottom of that the BLEU score is listed.