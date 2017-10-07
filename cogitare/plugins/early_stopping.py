from cogitare.core import PluginInterface
import numpy as np
from cogitare.utils import StopTraining


class EarlyStopping(PluginInterface):
    """
    This plugin provides the early stopping algorithm.

    During training, it will check the validation loss and if after ``max_tries``
    epochs the validation loss does not decrease, the training stops.

    The parameters with the best score found is saved in disk using :func:`torch.save` in the
    provided ``path``.

    When stopping, the plugin will automatically restore the model to the best checkpoint. If
    you don't want to have this feature, set ``restore_checkpoint=False``.

    It's recommended to use this plugin at the **on_end_epoch** hook since the validation loss
    is calculated at this point.


    Args:
        max_tries (int): number of epochs before stopping the training
        path (str): path to save the best model
        name (str): the name of the variable used to use as a metric. As default,
            get the loss in the validation dataset.
        func (callabe): function to apply in the incoming data (useful for computing
            the mean/norm/min/max of vectors to use as a metric, and defaults
            on :func:`numpy.mean`.
        restore_checkpoint (bool): if True,  restore the model parameters after stopping by
            early-stopping.
        freq (int): the frequency to execute this model. The model will execute at each ``freq`` call.

    Example::

        metrics = {
            'loss': model.metric_loss,
            'precision': precision
        }
        ev = Evaluator(validation_dataset, metrics)

        # by default, the EarlyStopping uses the Evaluator "loss" metric.
        early = EarlyStopping(max_tries=10, path='/tmp/model.pt')

        # to use a different metric, use:
        early = EarlyStopping(max_tries=10, path='/tmp/model.pt',
                              name='on_end_batch_Evaluator_precision')
        model.register_plugin([ev, early], 'on_end_epoch')
    """

    def __init__(self, max_tries, path, name='on_end_epoch_Evaluator_loss',
                 func=np.mean, restore_checkpoint=True, freq=1):
        super(EarlyStopping, self).__init__(freq=freq)
        self.max_tries = max_tries
        self.path = path
        self.restore_checkpoint = restore_checkpoint
        self.metric_name = name
        if not func:
            def func(x): return x
        self.func = func

        self._best_epoch = 0
        self._best_score = float('inf')

    def function(self, model, current_epoch, **kwargs):
        metric = self.func(kwargs.get(self.metric_name))

        if metric < self._best_score:
            self._best_score = metric

            model.save(self.path)
            self._best_epoch = current_epoch
        elif current_epoch - self._best_epoch > self.max_tries:
            print('\n\nStopping training after %d tries. Best score %.4f' % (
                self.max_tries, self._best_score))

            if self.restore_checkpoint:
                model.load(self.path)
                print('Model restored from: ' + self.path)

            raise StopTraining
