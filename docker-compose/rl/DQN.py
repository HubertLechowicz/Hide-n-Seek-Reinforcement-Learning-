from . import TrainingAlgorithm

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np


def create_q_model(n_inputs, n_outputs):
    # Network defined by the Deepmind paper
    inputs = layers.Input(n_inputs)

    # Convolutions on the frames on the screen
    layer1 = layers.Dense(32, activation="relu")(inputs)
    layer2 = layers.Dense(64, activation="relu")(layer1)
    layer3 = layers.Dense(64, activation="relu")(layer2)
    layer4 = layers.Dense(64, activation="relu")(layer3)
    layer5 = layers.Dense(512, activation="relu")(layer4)
    action = layers.Dense(n_outputs, activation="linear")(layer5)

    return keras.Model(inputs=inputs, outputs=action)


class DQN(TrainingAlgorithm):
    def __init__(self, env, num_agents, gamma, epsilon, epsilon_min,
                 epsilon_max, batch_size, n_inputs_n, n_outputs):
        super().__init__()
        self.env = env

        # Configuration paramaters for the whole setup
        self.gamma = gamma  # Discount factor for past rewards
        self.num_agents = num_agents

        self.epsilon_min = epsilon_min  # Minimum epsilon greedy parameter
        self.epsilon_max = epsilon_max  # Maximum epsilon greedy parameter
        self.epsilon_interval = (
                self.epsilon_max - self.epsilon_min
        )  # Rate at which to reduce chance of random action being taken
        self.batch_size = batch_size  # Size of batch taken from replay buffer
        self.n_inputs_n = n_inputs_n  # observation space
        self.n_outputs = n_outputs  # action space

        # prepare_model
        self.model_n = None
        self.model_target_n = None
        self.epsilon = epsilon  # Epsilon greedy parameter

        # In the Deepmind paper they use RMSProp however then Adam optimizer
        # improves training time
        self.optimizer_n = None

        # Experience replay buffers
        self.action_history_n = None
        self.rewards_history_n = None
        self.state_history_n = None
        self.done_history_n = None
        self.episode_reward_history_n = None
        # Number of frames to take random action and observe output
        self.epsilon_random_frames = None
        # Number of frames for exploration
        self.epsilon_greedy_frames = None
        # Maximum replay length
        # Note: The Deepmind paper suggests 1000000 however this causes memory issues
        self.max_memory_length_n = None
        # Train the model after 4 actions
        self.update_after_actions_n = None
        # How often to update the target network
        self.update_target_network_n = None
        # Using huber loss for stability
        self.loss_function_n = None

        # before episode
        self.episode_reward_n = None

        self.state_next_history_n = None

    def prepare_model(self, *args, **kwargs):
        # The first model makes the predictions for Q-values which are used to
        # make a action.
        self.model_n = [create_q_model(self.n_inputs_n[j], self.n_outputs) for j in range(self.num_agents)]
        # Build a target model for the prediction of future rewards.
        # The weights of a target model get updated every 10000 steps thus when the
        # loss between the Q-values is calculated the target Q-value is stable.
        self.model_target_n = [create_q_model(self.n_inputs_n[j], self.n_outputs) for j in range(self.num_agents)]
        # Number of frames to take random action and observe output
        self.epsilon_random_frames = round(self.env.cfg['duration'] * 0.05)
        # Number of frames for exploration
        self.epsilon_greedy_frames = round(self.env.cfg['duration'] * 0.2)
        # Maximum replay length
        # Note: The Deepmind paper suggests 1000000 however this causes memory issues
        self.max_memory_length_n = [100000 for _ in range(self.num_agents)]
        # Train the model after 4 actions
        self.update_after_actions_n = [100 for _ in range(self.num_agents)]
        # How often to update the target network
        self.update_target_network_n = [1000 for _ in range(self.num_agents)]
        # Using huber loss for stability
        self.loss_function_n = \
            [keras.losses.Huber() for _ in range(self.num_agents)]
        # ---
        self.state_history_n = [[] for _ in range(self.num_agents)]
        self.state_next_history_n = [[] for _ in range(self.num_agents)]

        self.optimizer_n = [keras.optimizers.Adam(learning_rate=0.00025, clipnorm=1.0) for _ in range(self.num_agents)]
        self.action_history_n = [[] for _ in range(self.num_agents)]
        self.rewards_history_n = [[] for _ in range(self.num_agents)]
        self.done_history_n = [[] for _ in range(self.num_agents)]
        self.episode_reward_history_n = [[] for _ in range(self.num_agents)]

    def before_episode(self, *args, **kwargs):
        self.episode_reward_n = [0 for _ in range(self.num_agents)]

    def before_action(self, *args, **kwargs):
        pass

    def take_action(self, *args, **kwargs):
        # Use epsilon-greedy for exploration
        if self.env.cfg['duration'] - self.env.duration < self.epsilon_random_frames \
                or self.epsilon > np.random.rand(1)[0]:
            # Take random action
            action_n = [np.random.choice(self.n_outputs) for _ in range(self.num_agents)]
            _ = [self.action_history_n[j].append(action_n[j]) for j in range(self.num_agents)]

            return action_n
        else:
            # Predict action Q-values
            # From environment state
            action_n = []
            for j in range(self.num_agents):
                state_tensor = tf.convert_to_tensor(kwargs['obs_n'][j])
                state_tensor = tf.expand_dims(state_tensor, 0)
                action_probs = self.model_n[j](state_tensor, training=False)
                # Take best action
                action_n.append(tf.argmax(action_probs[0]).numpy())
                self.action_history_n[j].append(action_n[j])
            return action_n

    def before_step(self, *args, **kwargs):
        # Decay probability of taking random action
        self.epsilon -= self.epsilon_interval / self.epsilon_greedy_frames
        self.epsilon = max(self.epsilon, self.epsilon_min)

    def after_step(self, *args, **kwargs):
        for j in range(self.num_agents):
            self.episode_reward_n[j] = kwargs['reward_n'][j]

            # =====================================================================
            # Save actions and states in replay buffer
            self.rewards_history_n[j].append(kwargs['reward_n'][j])
            self.state_history_n.append(kwargs['obs_old_n'][j])
            self.state_next_history_n.append(kwargs['obs_n'][j])
            self.done_history_n.append(kwargs['done'][0])

            # Update every fourth frame and once batch size is over 32
            if (self.env.cfg['duration'] - self.env.duration) % self.update_after_actions_n[j] == 0 \
                    and len(self.done_history_n[j]) > self.batch_size:
                # Get indices of samples for replay buffers
                indices = np.random.choice(range(len(self.done_history_n[j])), size=self.batch_size)

                # Using list comprehension to sample from replay buffer
                state_sample = np.array([self.state_history_n[j][i] for i in indices])
                state_next_sample = np.array([self.state_next_history_n[j][i] for i in indices])
                rewards_sample = [self.rewards_history_n[j][i] for i in indices]
                action_sample = [self.action_history_n[j][i] for i in indices]
                done_sample = tf.convert_to_tensor(
                    [float(self.done_history_n[j][i]) for i in indices]
                )

                # Build the updated Q-values for the sampled future states
                # Use the target model for stability
                future_rewards = self.model_target_n[j].predict(state_next_sample)
                # Q value = reward + discount factor * expected future reward
                updated_q_values = rewards_sample + self.gamma * tf.reduce_max(
                    future_rewards, axis=1
                )

                # If final frame set the last value to -1
                updated_q_values = updated_q_values * (1 - done_sample) - done_sample

                # Create a mask so we only calculate loss on the updated Q-values
                masks = tf.one_hot(action_sample, self.n_outputs)

                with tf.GradientTape() as tape:
                    # Train the model on the states and updated Q-values
                    q_values = self.model_n[j](state_sample)

                    # Apply the masks to the Q-values to get the Q-value for action taken
                    q_action = tf.reduce_sum(tf.multiply(q_values, masks), axis=1)
                    # Calculate loss between new Q-value and old Q-value
                    loss = self.loss_function_n(updated_q_values, q_action)

                # Backpropagation
                grads = tape.gradient(loss, self.model_n[j].trainable_variables)
                self.optimizer_n[j].apply_gradients(zip(grads, self.model_n[j].trainable_variables))

            if (self.env.cfg['duration'] - self.env.duration) % self.update_target_network_n[j] == 0:
                # update the the target network with new weights
                self.model_target_n[j].set_weights(self.model_n[j].get_weights())

            # Limit the state and reward history
            if len(self.rewards_history_n[j]) > self.max_memory_length_n[j]:
                del self.rewards_history_n[j][:1]
                del self.state_history_n[j][:1]
                del self.action_history_n[j][:1]
                del self.done_history_n[j][:1]

    def handle_gameover(self, *args, **kwargs):
        pass

    def after_episode(self, *args, **kwargs):
        for j in range(self.num_agents):
            self.episode_reward_history_n[j].append(self.episode_reward_n[j])
            if len(self.episode_reward_history_n[j]) > 100:
                del self.episode_reward_history_n[j][:1]

    def before_cleanup(self, *args, **kwargs):
        pass

    def __str__(self):
        return "DQN Algorithm Class"
