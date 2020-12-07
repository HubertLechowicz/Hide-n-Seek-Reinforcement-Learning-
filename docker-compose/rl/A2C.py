from . import TrainingAlgorithm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
import torch.nn.functional as F

import numpy as np

class ActorCritic(nn.Module):
    def __init__(self, num_inputs, num_actions, hidden_size, learning_rate=3e-4):
        super(ActorCritic, self).__init__()

        self.num_actions = num_actions
        self.critic_linear1 = nn.Linear(num_inputs, hidden_size)
        self.critic_linear2 = nn.Linear(hidden_size, 1)

        self.actor_linear1 = nn.Linear(num_inputs, hidden_size)
        self.actor_linear2 = nn.Linear(hidden_size, num_actions)

    def forward(self, state):
        state = Variable(torch.from_numpy(state).float().unsqueeze(0))
        value = F.relu(self.critic_linear1(state))
        value = self.critic_linear2(value)

        policy_dist = F.relu(self.actor_linear1(state))
        policy_dist = F.softmax(self.actor_linear2(policy_dist), dim=1)

        return value, policy_dist


class A2C(TrainingAlgorithm):
    def __init__(self, env, num_agents, gamma, hidden_size, l_rate, n_inputs_n, n_outputs):
        # https://towardsdatascience.com/understanding-actor-critic-methods-931b97b6df3f
        self.env = env
        
        # consts
        self.gamma = gamma
        self.num_agents = num_agents
        self.hidden_size = hidden_size
        self.learning_rate = l_rate
        self.num_inputs_n = n_inputs_n # observation space
        self.num_outputs = n_outputs # action space

        # prepare_model
        self.actor_critic_n = None
        self.ac_optimizer_n = None
        self.all_lengths_n = None
        self.average_lengths_n = None
        self.all_rewards_n = None
        self.entropy_term_n = None

        # before_episode, reset in after_episode
        self.log_probs_n = None
        self.values_n = None
        self.rewards_n = None

        # before_action, changes every frame
        self.value_n = None
        self.policy_dist_n = None
        self.dist_n = None

        # take_action
        self.action_n = None

        # before_step
        self.log_prob_n = None
        self.entropy_n = None

        # after_step, appending to values from before_episode and prepare_model
        
        # handle_gameover
        self.qval_n = None

        # after_episode
        self.qvals_n = None

        # before_cleanup

    def prepare_model(self, *args, **kwargs):
        self.actor_critic_n = [ActorCritic(self.num_inputs_n[j], self.num_outputs, self.hidden_size) for j in range(self.num_agents)]
        self.ac_optimizer_n = [optim.Adam(self.actor_critic_n[j].parameters(), lr=self.learning_rate) for j in range(self.num_agents)]
        self.all_lengths_n = [[], []]
        self.average_lengths_n = [[], []]
        self.all_rewards_n = [[], []]
        self.entropy_term_n = [0, 0]

    def before_episode(self, *args, **kwargs):
        self.log_probs_n = [[], []]
        self.values_n = [[], []]
        self.rewards_n =  [[], []]

    def before_action(self, *args, **kwargs):
        self.value_n = [None, None]
        self.policy_dist_n = [None, None]

        for j in range(self.num_agents):
            self.value_n[j], self.policy_dist_n[j] = self.actor_critic_n[j].forward(kwargs['obs_n'][j])

        self.value_n = [val.detach().numpy()[0, 0] for val in self.value_n]
        self.dist_n = [pol_dist.detach().numpy() for pol_dist in self.policy_dist_n]

    def take_action(self, *args, **kwargs):
        return [np.random.choice(self.num_outputs, p=np.squeeze(self.dist_n[j])) for j in range(self.num_agents)]

    def before_step(self, *args, **kwargs):
        self.log_prob_n = [torch.log(self.policy_dist_n[j].squeeze(0)[kwargs['action_n'][j]]) for j in range(self.num_agents)]
        self.entropy_n = [-np.sum(np.mean(self.dist_n[j]) * np.log(self.dist_n[j])) for j in range(self.num_agents)]

    def after_step(self, *args, **kwargs):
        for j in range(self.num_agents):
            self.rewards_n[j].append(kwargs['reward_n'][j])
            self.values_n[j].append(self.value_n[j])
            self.log_probs_n[j].append(self.log_prob_n[j])
            self.entropy_term_n[j] += self.entropy_n[j]

    def handle_gameover(self, *args, **kwargs):
        self.qval_n = [None, None]
        for j in range(self.num_agents):
            qval, _ = self.actor_critic_n[j].forward(kwargs['obs_n'][j])
            qval = qval.detach().numpy()[0, 0]
            self.qval_n[j] = qval
            self.all_rewards_n[j].append(np.sum(self.rewards_n[j]))
            self.all_lengths_n[j].append(kwargs['ep_length'])
            self.average_lengths_n[j].append(np.mean(self.all_lengths_n[j][-10:]))

    def after_episode(self, *args, **kwargs):
        self.qvals_n = [None, None]
        for j in range(self.num_agents):
            self.qvals_n[j] = np.zeros_like(self.values_n[j])
            for t in reversed(range(len(self.rewards_n[j]))):
                self.qval_n[j] = self.rewards_n[j][t] + self.gamma * self.qval_n[j]
                self.qvals_n[j][t] = self.qval_n[j]
            self.values_n[j] = torch.FloatTensor(self.values_n[j])
            self.qvals_n[j] = torch.FloatTensor(self.qvals_n[j])
            self.log_probs_n[j] = torch.stack(self.log_probs_n[j])

            advantage = self.qvals_n[j] - self.values_n[j]
            actor_loss = (-self.log_probs_n[j] * advantage).mean()
            critic_loss = 0.5 * advantage.pow(2).mean()
            ac_loss = actor_loss + critic_loss + 0.001 * self.entropy_term_n[j]

            self.ac_optimizer_n[j].zero_grad()
            ac_loss.backward()
            self.ac_optimizer_n[j].step()

    def before_cleanup(self, *args, **kwargs):
        pass

    def __str__(self):
        return "A2C Class"