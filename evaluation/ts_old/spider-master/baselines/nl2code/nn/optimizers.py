from __future__ import absolute_import
import theano
import theano.tensor as T

from .utils.theano_utils import shared_zeros, shared_scalar, floatX
from .utils.generic_utils import get_from_module
from six.moves import zip
from theano.sandbox.rng_mrg import MRG_RandomStreams
from theano.tensor.shared_randomstreams import RandomStreams
import math
from nn.utils.config_factory import config


def clip_norm(g, c, n):
    if c > 0:
        g = T.switch(T.ge(n, c), g * c / n, g)
    return g


def kl_divergence(p, p_hat):
    return p_hat - p + p * T.log(p / p_hat)


class Optimizer(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.updates = []

    def get_state(self):
        return [u[0].get_value() for u in self.updates]

    def set_state(self, value_list):
        assert len(self.updates) == len(value_list)
        for u, v in zip(self.updates, value_list):
            u[0].set_value(floatX(v))

    def get_updates(self, params, constraints, loss, **kwargs):
        raise NotImplementedError

    def get_gradients(self, loss, params, **kwargs):

        grads = T.grad(loss, params, disconnected_inputs='warn', **kwargs)

        if hasattr(self, 'clip_grad') and self.clip_grad > 0:
            norm = T.sqrt(sum([T.sum(g ** 2) for g in grads]))
            # norm = theano.printing.Print('gradient norm::')(norm)
            grads = [clip_norm(g, self.clip_grad, norm) for g in grads]

        return grads

    def get_config(self):
        return {"name": self.__class__.__name__}


class SGD(Optimizer):

    def __init__(self, lr=0.01, momentum=0., decay=0., nesterov=False, *args, **kwargs):
        super(SGD, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = shared_scalar(0)
        self.lr = shared_scalar(lr)
        self.momentum = shared_scalar(momentum)

    def get_updates(self, params, loss):
        grads = self.get_gradients(loss, params)
        lr = self.lr * (1.0 / (1.0 + self.decay * self.iterations))
        self.updates = [(self.iterations, self.iterations + 1.)]

        for p, g in zip(params, grads):
            m = shared_zeros(p.get_value().shape)  # momentum
            v = self.momentum * m - lr * g  # velocity
            self.updates.append((m, v))

            if self.nesterov:
                new_p = p + self.momentum * v - lr * g
            else:
                new_p = p + v

            self.updates.append((p, new_p))
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "momentum": float(self.momentum.get_value()),
                "decay": float(self.decay.get_value()),
                "nesterov": self.nesterov}


class RMSprop(Optimizer):
    def __init__(self, lr=0.001, rho=0.9, epsilon=1e-6, *args, **kwargs):
        super(RMSprop, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)
        self.rho = shared_scalar(rho)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = self.rho * a + (1 - self.rho) * g ** 2  # update accumulator
            self.updates.append((a, new_a))

            new_p = p - self.lr * g / T.sqrt(new_a + self.epsilon)
            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "rho": float(self.rho.get_value()),
                "epsilon": self.epsilon}


class Adagrad(Optimizer):
    def __init__(self, lr=0.01, epsilon=1e-6, *args, **kwargs):
        super(Adagrad, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = a + g ** 2  # update accumulator
            self.updates.append((a, new_a))
            new_p = p - self.lr * g / T.sqrt(new_a + self.epsilon)
            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "epsilon": self.epsilon}


class Adadelta(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1212.5701
    '''
    def __init__(self, lr=1.0, rho=0.95, epsilon=1e-6, *args, **kwargs):
        super(Adadelta, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)

    def get_updates(self, params, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        delta_accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []

        for p, g, a, d_a in zip(params, grads, accumulators, delta_accumulators):
            new_a = self.rho * a + (1 - self.rho) * g ** 2  # update accumulator
            self.updates.append((a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g * T.sqrt(d_a + self.epsilon) / T.sqrt(new_a +
                                                             self.epsilon)

            new_p = p - self.lr * update
            self.updates.append((p, new_p))

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * update ** 2
            self.updates.append((d_a, new_d_a))
        return self.updates, grads

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "rho": self.rho,
                "epsilon": self.epsilon}


class Adadelta_GaussianNoise(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1212.5701
    '''
    def __init__(self, lr=1.0, rho=0.95, epsilon=1e-6, *args, **kwargs):
        super(Adadelta_GaussianNoise, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)
        self.rng = MRG_RandomStreams(use_cuda=config.get('run.use_cuda')) #RandomStreams() #(use_cuda=False)

    def get_updates(self, params, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        delta_accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []
        n_step = theano.shared(1.0)
        self.updates.append((n_step, n_step + 1))

        for p, g, a, d_a in zip(params, grads, accumulators, delta_accumulators):
            g_noise = self.rng.normal(p.shape, 0, T.sqrt(n_step ** - 0.55), dtype='float32')
            g_deviated = g + g_noise

            new_a = self.rho * a + (1 - self.rho) * g_deviated ** 2  # update accumulator
            self.updates.append((a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g_deviated * T.sqrt(d_a + self.epsilon) / T.sqrt(new_a +
                                                             self.epsilon)

            new_p = p - self.lr * update
            self.updates.append((p, new_p))

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * update ** 2
            self.updates.append((d_a, new_d_a))
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "rho": self.rho,
                "epsilon": self.epsilon}


class Adam(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1412.6980v8

        Default parameters follow those provided in the original paper.
    '''
    def __init__(self, lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-8, *args, **kwargs):
        super(Adam, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = shared_scalar(0)
        self.lr = shared_scalar(lr)
        # self.rng = MRG_RandomStreams(use_cuda=config['use_gpu']) #RandomStreams() #(use_cuda=False)

    def get_updates(self, params, loss, **kwargs):
        grads = self.get_gradients(loss, params, **kwargs)
        self.updates = [(self.iterations, self.iterations+1.)]

        t = self.iterations + 1
        lr_t = self.lr * T.sqrt(1-self.beta_2**t)/(1-self.beta_1**t)

        # n_step = theano.shared(1.0)
        # self.updates.append((n_step, n_step + 1))

        gradients = []

        for p, g in zip(params, grads):
            m = theano.shared(p.get_value() * 0.)  # zero init of moment
            v = theano.shared(p.get_value() * 0.)  # zero init of velocity

            # g_noise = self.rng.normal(g.shape, 0, T.sqrt(0.5 * n_step ** - 0.55), dtype='float32')
            # g_deviated = g + g_noise
            g_deviated = g

            # for debug purposes
            gradients.append(g)

            m_t = (self.beta_1 * m) + (1 - self.beta_1) * g_deviated
            v_t = (self.beta_2 * v) + (1 - self.beta_2) * (g_deviated**2)
            p_t = p - lr_t * m_t / (T.sqrt(v_t) + self.epsilon)

            self.updates.append((m, m_t))
            self.updates.append((v, v_t))
            self.updates.append((p, p_t))  # apply constraints
        return self.updates, gradients

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "beta_1": self.beta_1,
                "beta_2": self.beta_2,
                "epsilon": self.epsilon}

# aliases
sgd = SGD
rmsprop = RMSprop
adagrad = Adagrad
adadelta = Adadelta
adam = Adam
adadelta_noise = Adadelta_GaussianNoise


def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'optimizer', instantiate=True,
                           kwargs=kwargs)
