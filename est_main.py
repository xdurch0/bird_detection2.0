import os

import numpy as np
import tensorflow as tf

from data_utils import read_data_config, make_labeled_data_list
from est_input import input_fn
from est_models import model_fn
from utils import checkpoint_iterator


def run_birds(mode, data_config, model_config, model_dir,
              act, batchnorm,
              adam_params, augment, batch_size, clipping, data_format,
              label_smoothing, normalize, onedim, reg, renorm, steps,
              threshold, use_avg, vis):
    """
    All of these parameters can be passed from est_cli. Please check
    that one for docs on what they are.
    
    Returns:
        Depends on mode!
        If train or eval: Nothing is returned.
        If predict: Returns a generator over predictions for the test set.
        If return: Return the estimator object. Use this if you want access to
                   the variables or their values, for example.
    """
    # Set up, verify arguments etc.
    tf.logging.set_verbosity(tf.logging.INFO)

    config_dict = read_data_config(data_config)
    tfr_path = config_dict["tfr_path"]

    if "mel_freqs" in config_dict:
        freqs = config_dict["mel_freqs"]
    elif "window_size" in config_dict:
        freqs = config_dict["window_size"] // 2 + 1
    else:
        freqs = 1

    if act == "elu":
        act = tf.nn.elu
    else:  # since no other choice is allowed
        act = tf.nn.relu

    params = {"model_config": model_config,
              "act": act,
              "use_bn": batchnorm,
              "data_format": data_format,
              "adam_args": adam_params,
              "clipping": clipping,
              "vis": vis,
              "reg": reg,
              "onedim": onedim,
              "label_smoothing": label_smoothing,
              "normalize": normalize,
              "renorm": renorm,
              "use_avg": use_avg}

    # we set infrequent "permanent" checkpoints
    # we also disable the default SummarySaverHook IF profiling is requested
    config = tf.estimator.RunConfig(keep_checkpoint_every_n_hours=1,
                                    save_summary_steps=vis or 100,
                                    save_checkpoints_steps=500,
                                    keep_checkpoint_max=1000,
                                    model_dir=model_dir)
    estimator = tf.estimator.Estimator(model_fn=model_fn,
                                       params=params,
                                       config=config)
    if mode == "return":
        return estimator

    if mode == "train":
        def train_input_fn(): return input_fn(
            tfr_path, "train", freqs=freqs, batch_size=batch_size,
            augment=augment, threshold=threshold)

        logging_hook = tf.train.LoggingTensorHook(
            {"eval/accuracy": "eval/batch_accuracy"},
            every_n_iter=vis,
            at_end=True)
        estimator.train(input_fn=train_input_fn, steps=steps,
                        hooks=[logging_hook])

    elif mode == "eval":
        def eval_input_fn():
            return input_fn(
                tfr_path, "dev", freqs=freqs, batch_size=batch_size,
                augment=False, threshold=threshold)

        for ckpt in checkpoint_iterator(os.path.join(model_dir, "checkpoint")):
            print("Evaluating checkpoint {}...".format(ckpt))
            eval_results = estimator.evaluate(input_fn=eval_input_fn)
            print("Evaluation results:\n", eval_results)
        return

    elif mode == "predict":
        def eval_input_fn():
            return input_fn(
                tfr_path, "dev", freqs=freqs, batch_size=batch_size,
                augment=False, threshold=threshold)

        orig_data = make_labeled_data_list(
            config_dict["data_dir"], config_dict["datasets"])
        dev_inds = set(np.load(config_dict["dev_inds"]))
        dev_data = [d for i, d in enumerate(orig_data) if i in dev_inds]

        def gen():
            for data, predictions in zip(
                    dev_data, estimator.predict(input_fn=eval_input_fn)):
                predictions_repacked = dict()

                # construct a sorted list of layers and their activations, with
                # input and front
                layers = [(n, a) for (n, a) in predictions.items() if
                          leading_string(n) in ["layer", "pool"]]
                layers.sort(key=lambda tup: trailing_num(tup[0]))
                layers.insert(0, ("input", predictions["input"]))

                predictions_repacked["all_layers"] = layers
                for k in ["flattened", "logits", "probabilities", "classes"]:
                    predictions_repacked[k] = predictions[k]
                predictions_repacked["label"] = data[1]
                predictions_repacked["file"] = data[0]
                yield predictions_repacked
        return gen()

    else:
        print("Mode unknown. Doing nothing...")
        return


###############################################################################
# HELPERS
###############################################################################
def leading_string(string):
    """Splits e.g. "layer104" into "layer", "104" an returns "layer"."""
    alpha = string.rstrip('0123456789')
    return alpha


def trailing_num(string):
    """Splits e.g. "layer104" into "layer", "104" an returns int("104")."""
    alpha = string.rstrip('0123456789')
    num = string[len(alpha):]
    return int(num)
