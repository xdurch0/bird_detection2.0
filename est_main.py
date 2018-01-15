import tensorflow as tf

from data_utils import read_data_config
from est_input import input_fn
from est_models import model_fn


def run_birds(mode, data_config, model_config, model_dir,
              act, batchnorm,
              adam_params, augment, batch_size, clipping, data_format, reg,
              steps_train, steps_eval, vis):
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
              "reg": reg}

    # we set infrequent "permanent" checkpoints
    # we also disable the default SummarySaverHook IF profiling is requested
    config = tf.estimator.RunConfig(keep_checkpoint_every_n_hours=1,
                                    save_summary_steps=vis or 100,
                                    model_dir=model_dir)
    estimator = tf.estimator.Estimator(model_fn=model_fn,
                                       params=params,
                                       config=config)
    if mode == "return":
        return estimator

    def eval_input_fn(): return input_fn(
        tfr_path, "dev", freqs=freqs, batch_size=batch_size, augment=False)

    if mode == "train":
        def train_input_fn(): return input_fn(
            tfr_path, "train", freqs=freqs, batch_size=batch_size,
            augment=augment)

        logging_hook = tf.train.LoggingTensorHook(
            {"eval/accuracy": "eval/batch_accuracy"},
            every_n_iter=vis,
            at_end=True)
        steps_taken = 0
        while steps_taken < steps_train:
            estimator.train(input_fn=train_input_fn, steps=steps_eval,
                            hooks=[logging_hook])
            steps_taken += steps_eval
            estimator.evaluate(input_fn=eval_input_fn)

    elif mode == "eval":
        eval_results = estimator.evaluate(input_fn=input_fn)
        print("Evaluation results:\n", eval_results)
        return

    else:
        print("Mode unknown. Doing nothing...")
        return
