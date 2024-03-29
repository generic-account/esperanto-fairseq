SEED=101
DEVICE=0
src="eo"
tgt="en"

pair="${src}-${tgt}"
EXPERIMENT_NAME="semantic_tokenizer_test_${pair}_${SEED}"


TEXT=/home/marco/github/EsperantoTokenization/data/esperanto_tokenizer
fairseq-preprocess --source-lang $src --target-lang $tgt \
    --trainpref $TEXT/train --validpref $TEXT/valid --testpref $TEXT/test \
    --destdir data-bin/${EXPERIMENT_NAME}.${pair} \
    --workers 10

cd ../..

mkdir experiment_outputs/${EXPERIMENT_NAME}

CUDA_VISIBLE_DEVICES=$DEVICE fairseq-train  examples/esperanto/data-bin/${EXPERIMENT_NAME}.${pair} \
                                            --arch transformer_iwslt_de_en \
                                            --share-decoder-input-output-embed \
                                            --optimizer adam --adam-betas '(0.9, 0.98)' \
                                            --clip-norm 0.0 \
                                            --lr 5e-4 \
                                            --lr-scheduler inverse_sqrt \
                                            --warmup-updates 4000 \
                                            --dropout 0.3 \
                                            --weight-decay 0.0001 \
                                            --criterion label_smoothed_cross_entropy \
                                            --label-smoothing 0.1 \
                                            --max-tokens 4096 \
                                            --eval-bleu  \
                                            --eval-bleu-args '{"beam": 5, "max_len_a": 1.2, "max_len_b": 10}' \
                                            --eval-bleu-detok "moses" \
                                            --eval-bleu-remove-bpe \
                                            --esperanto-tokenizer-type "semantic" \
                                            --eval-bleu-print-samples \
                                            --best-checkpoint-metric bleu \
                                            --maximize-best-checkpoint-metric \
                                            --patience 5  \
                                            --save-dir "experiment_outputs/${EXPERIMENT_NAME}" \
                                            --source-lang=$src \
                                            --target-lang=$tgt \
                                            --task "translation" \
                                            --seed $SEED \
                                            --no-epoch-checkpoints > experiment_outputs/${EXPERIMENT_NAME}/$EXPERIMENT_NAME.log

CUDA_VISIBLE_DEVICES=$DEVICE fairseq-generate examples/esperanto/data-bin/${EXPERIMENT_NAME}.${pair} \
                                        --path experiment_outputs/${EXPERIMENT_NAME}/checkpoint_best.pt \
                                        --batch-size 128 \
                                        --beam 5 \
                                        --max-len-a 1.2 \
                                        --max-len-b 10 \
                                        --remove-bpe \
                                        --esperanto-tokenizer-type "semantic" > experiment_outputs/${EXPERIMENT_NAME}/bleu.log

