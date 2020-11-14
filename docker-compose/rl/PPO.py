from . import TrainingAlgorithm


import torch.optim as optim
from torch.autograd import Variable


import torch
import torch.nn as nn
from torch.distributions import Categorical


device = "cpu"


class Memory:
    def __init__(self):
        self.actions = []
        self.states = []
        self.logprobs = []
        self.rewards = []
        self.is_terminals = []

    def clear_memory(self):
        del self.actions[:]
        del self.states[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.is_terminals[:]


class ActorCritic(nn.Module):
    def __init__(self, n_inputs_n, n_outputs, hidden_size):
        super(ActorCritic, self).__init__()

        # actor
        self.action_layer = nn.Sequential(
            nn.Linear(n_inputs_n, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, n_outputs),
            nn.Softmax(dim=-1)
        )

        # critic
        self.value_layer = nn.Sequential(
            nn.Linear(n_inputs_n, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )


    def forward(self):
        raise NotImplementedError

    def act(self, state, memory):
        state = torch.from_numpy(state).float().to(device)
        action_probs = self.action_layer(state)
        dist = Categorical(action_probs)
        action = dist.sample()

        memory.states.append(state)
        memory.actions.append(action)
        memory.logprobs.append(dist.log_prob(action))

        return action.item()

    def evaluate(self, state, action):
        action_probs = self.action_layer(state)
        dist = Categorical(action_probs)

        action_logprobs = dist.log_prob(action)
        dist_entropy = dist.entropy()

        state_value = self.value_layer(state)

        return action_logprobs, torch.squeeze(state_value), dist_entropy


class PPO(TrainingAlgorithm):
    def __init__(self, env, num_agents, gamma, hidden_size, l_rate, n_inputs_n, n_outputs, betas, K_epochs, eps_clip, update_timestep):
        super().__init__()

        # https://github.com/nikhilbarhate99/PPO-PyTorch/blob/master/PPO.py
        self.env = env  # A2C

        # consts
        self.l_rate = l_rate
        self.betas = betas
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs
        self.num_agents = num_agents
        self.num_inputs_n = n_inputs_n  # observation space
        self.num_outputs = n_outputs  # action space
        self.hidden_size = hidden_size

        # prepare_model
        self.policy_n = None
        self.optimizer_n = None
        self.policy_old_n  = None
        self.MseLoss = None
        self.all_lengths_n = None
        self.average_lengths_n = None
        self.all_rewards_n = None
        self.entropy_term_n = None
        self.memory_n = None

        # before_episode
        self.rewards_n = None
        self.discounted_reward_n = None

        #after step
        self.update_timestep = update_timestep

    def prepare_model(self, *args, **kwargs):
        self.memory_n = [Memory() for _ in range(self.num_agents)]
        self.policy_n = [ActorCritic(self.num_inputs_n[j], self.num_outputs, self.hidden_size).to(device) for j in range(self.num_agents)]
        self.optimizer_n = [optim.Adam(self.policy_n[j].parameters(), lr=self.l_rate, betas=self.betas) for j in range(self.num_agents)]
        self.policy_old_n = self.policy_n
        _ = [self.policy_old_n[j].load_state_dict(self.policy_n[j].state_dict()) for j in range(self.num_agents)]
        self.MseLoss = nn.MSELoss()

    def before_episode(self, *args, **kwargs):
        pass

    def before_action(self, *args, **kwargs):
        pass

    def take_action(self, *args, **kwargs):
        return [self.policy_old_n[j].act(kwargs['obs_n'][j], self.memory_n[j])  for j in range(self.num_agents)]

    def before_step(self, *args, **kwargs):
        pass

    def after_step(self, *args, **kwargs):
        cur_frame = self.env.cfg['duration'] - self.env.duration
        for j in range(self.num_agents):
            self.memory_n[j].rewards.append(kwargs['reward_n'][j])
            self.memory_n[j].is_terminals.append(kwargs['done'][0])
            if cur_frame % self.update_timestep == 0:
                self._update(self.memory_n[j], self.policy_n[j], self.policy_old_n[j], self.optimizer_n[j])
                self.memory_n[j].clear_memory()

    def handle_gameover(self, *args, **kwargs):
        pass

    def after_episode(self, *args, **kwargs):
        pass

    def before_cleanup(self, *args, **kwargs):
        pass

    def _update(self, memory, policy, policy_old, optimizer):
        # Monte Carlo estimate of state rewards:
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(memory.rewards), reversed(memory.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.insert(0, discounted_reward)

        # Normalizing the rewards:
        rewards = torch.tensor(rewards, dtype=torch.float32).to(device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)

        # convert list to tensor
        old_states = torch.stack(memory.states).to(device).detach()
        old_actions = torch.stack(memory.actions).to(device).detach()
        old_logprobs = torch.stack(memory.logprobs).to(device).detach()

        # Optimize policy for K epochs:
        for _ in range(self.K_epochs):
            # Evaluating old actions and values :
            logprobs, state_values, dist_entropy = policy.evaluate(old_states, old_actions)

            # Finding the ratio (pi_theta / pi_theta__old):
            ratios = torch.exp(logprobs - old_logprobs.detach())

            # Finding Surrogate Loss:
            advantages = rewards - state_values.detach()
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.eps_clip, 1 + self.eps_clip) * advantages
            loss = -torch.min(surr1, surr2) + 0.5 * self.MseLoss(state_values, rewards) - 0.01 * dist_entropy

            # take gradient step
            optimizer.zero_grad()
            loss.mean().backward()
            optimizer.step()

        # Copy new weights into old policy:
        policy_old.load_state_dict(policy.state_dict())