# command line interface for running ASR models
import argparse
from est_main import run_birds


parser = argparse.ArgumentParser()
parser.add_argument("mode",
                    choices=["train", "predict", "eval", "return"],
                    help="What to do. 'train', 'predict', 'eval' or "
                         "'return' The latter simply returns the estimator "
                         "object.")
parser.add_argument("data_config",
                    help="Path to data config file. See code for details.")
parser.add_argument("model_config",
                    help="Path to model config file. See code for details.")
parser.add_argument("model_dir",
                    help="Path to store checkpoints etc.")

parser.add_argument("-a", "--act",
                    default="relu",
                    choices=["relu", "elu"],
                    help="Which activation function to use. "
                         "Can be one of 'relu' (default),"
                         "or 'elu'.")
parser.add_argument("-b", "--batchnorm",
                    action="store_true",
                    help="Set to use batch normalization.")

parser.add_argument("-A", "--adam_params",
                    nargs=4,
                    type=float,
                    # these are *not* the TF defaults!!
                    default=[1e-3, 0.9, 0.9, 1e-8],
                    metavar=["adam_lr", "adam_eps"],
                    help="Learning rate, beta1 and beta2 and epsilon for "
                         "Adam.")
parser.add_argument("-B", "--batch_size",
                    type=int,
                    default=64,
                    help="Batch size. Default: 64.")
parser.add_argument("-C", "--clipping",
                    type=float,
                    default=0.0,
                    help="Global norm to clip gradients to. Default: 0 (no "
                         "clipping).")
parser.add_argument("-F", "--data_format",
                    default="channels_first",
                    choices=["channels_first", "channels_last"],
                    help="Data format. Either 'channels_first' "
                         "(default, recommended for GPU) "
                         "or 'channels_last', recommended for CPU.")
parser.add_argument("-G", "--augment",
                    action="store_true",
                    help="Use augmented training data. Will lead to a crash "
                         "if no such data is available!")
parser.add_argument("-R", "--reg",
                    type=float,
                    default=0.0,
                    help="Regularizer coefficient. Default: 0 (no "
                         "regularization). Currently does nothing!!")
parser.add_argument("-S", "--steps",
                    help="Number of training/eval steps to take. Give as "
                         "comma-separated values, e.g. 20000,1000. Default: "
                         "20000 training steps, with evaluation every 1000 "
                         "steps. Frequent evaluation slows down the process. "
                         "Ignored if doing prediction or evaluation.")
parser.add_argument("-V", "--vis",
                    type=int,
                    default=100,
                    help="If set, add visualizations of gradient norms and "
                         "activation distributions as well as graph profiling."
                         " This number signifies per how many steps you want "
                         "to add summaries. Profiling is added this many steps"
                         " times 50 (e.g. every 5000 steps if this is set to "
                         "100). Default: 100. Setting this to 0 will only plot"
                         " curves for loss and steps per second, every 100 "
                         "steps. This may result in faster execution.")
args = parser.parse_args()

steps_train, steps_eval = args.steps.split(",")
steps_train = int(steps_train)
steps_eval = int(steps_eval)

out = run_birds(mode=args.mode, data_config=args.data_config,
                model_config=args.model_config, model_dir=args.model_dir,
                act=args.act, batchnorm=args.batchnorm,
                adam_params=args.adam_params, augment=args.augment,
                batch_size=args.batch_size, clipping=args.clipping,
                data_format=args.data_format, reg=args.reg,
                steps_train=steps_train, steps_eval=steps_eval, vis=args.vis)
