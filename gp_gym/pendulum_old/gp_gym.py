"""
The purpose of this module is to encapsulate common Genetic Programming and OpenAI gym functions
to make them reusable in different environments.
"""

import gym
import numpy as np


def gen_init_pop(pop_size, T, F, max_depth, method, t_rate, p_type):
    return [gen_program(T, F, max_depth, method, t_rate, p_type) for _ in range(pop_size)]


def gen_program(T, F, max_depth, method, t_rate, p_type):
    """
    Generates a random program with a fixed max depth using the terminal and function sets. 
        Supported methods: full and growth.

        T: terminal set
        F: function set
        max_depth: maximum program depth
        method: "grow" | "full"
        t_rate: probability of generating a terminal (only used if method='grow')
        p_type: the Type of the program to generate
        return: a literal or a list that represents a program
    """

    p = None

    # Filter terminals to only include items of the specified type.
    filt_terms = list(dict(filter(lambda term: term[1]["type"]==p_type, T.items())).keys())

    # Check if function set is empty
    filt_funcs = []
    if len(F) > 0:
        filt_funcs = list(dict(filter(lambda func: func[1]["type"]==p_type, F.items())).keys())

    # Pick a random terminal or function
    if max_depth == 0 or (method == "grow" and t_rate > np.random.rand()):
        p = np.random.choice(filt_terms)
    else:
        if filt_funcs:
            # Generate function of correct arity and arg type
            func = np.random.choice(filt_funcs)
            arg_types = F[func]["arg_types"]
            args = [gen_program(T, F, max_depth-1, method, t_rate, arg_type) for arg_type in arg_types]
            p = [func] + args
        else:  # a function of the required type doesn't exist
            p = np.random.choice(filt_terms)

    return p


def run_ep_while_not_done(env, p, eval, render=False):
    net_reward = 0

    obs = env.reset()
    done = False

    while not done:
        if render:
            env.render()

        action = eval(p, obs)
        obs, reward, done, info = env.step(action)
        net_reward += reward

    return net_reward


def IFLTE(args):
    """ Implements the IFLTE function. """
    return args[2] if args[0] <= args[1] else args[3]


def select(pop, fit_scores):
    """
    Fitness Proportionate Selection (Roulette Wheel Selection).
    Picks a probabilistically fit individual from a population.

    pop: population of programs
    fit_scores: fitness scores of each program in the population (parallel array to pop)  
    """

    selected = None

    # Turn negative fitness scores to positive without losing relative fitness information
    fit_scores = np.array(fit_scores)
    if fit_scores[0] < 0:
        fit_scores = 1 / abs(fit_scores)

    F = sum(fit_scores)
    r = np.random.uniform(0, F)

    acc = 0
    i = 0
    while (not selected) and (i < len(fit_scores)):
        acc += fit_scores[i]
        if acc > r:
            selected = pop[i]
        else:
            i += 1

    return selected

def mutate(p, T, F, max_depth, method, t_rate):
    """
    Performs subtree mutation on p.
    In this version of the function, p is either:
     - a terminal
     - a function with 4 arguments

    p: program to mutate
    return: mutated program
    """

    mut_p = None

    # Mutate atom
    if type(p) is not list:
        mut_p = gen_program(T, F, max_depth, method, t_rate, T[p]["type"])
    
    # If function: mutate one of its arguments
    else:
        arity = F[p[0]]["arity"]
        r = np.random.randint(1, high=arity+1)

        mut_p = [gen_program(T, F, max_depth, method, 1.0, T[p[i]]["type"]) if i==r else p[i] for i in range(1, len(p))]
        mut_p.insert(0, p[0])

    return mut_p
