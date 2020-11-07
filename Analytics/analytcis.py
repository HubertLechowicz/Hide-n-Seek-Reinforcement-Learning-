import pandas as pd
import os
import json
from collections.abc import Iterable


def read_json(path_to_json = 'data/input/'):
    """
       Reads jsons in the specified dir
        Parameters
        ----------
            path_to_json : string


        Returns
        -------
            List of jsons.
    """
    data = []
    for file_name in [file for file in os.listdir(path_to_json) if file.endswith('.json')]:
        with open(path_to_json + file_name) as json_file:
            data.append(json.load(json_file))
            return data

def parse_json_2_dataframe(jsons,unwanted_col = 'unwanted_col'):
    """
       Reads jsons in the specified dir
        Parameters
        ----------
            jsons : List of jsons.

            list_of_cols : list of columns from which DataFrame is made.

            unwanted_col : OPTIONAL, str.

            dataframe_aborted_cols : OPTIONAL, list of aborted columns



        Returns
        -------
            cleaned_dataframe : pd.DataFrame    N long table, N is number of episodes in the data.

            config_and_best : pd.DataFrame      table, with overall settings and best episode for each agent.
    """
    for json in jsons:
        list_of_cols = []
        dataframe_aborted_cols = []
        for key in json:
            if not isinstance(json[key], float):
                if key != unwanted_col:
                    col = pd.Series(json[key],name=key)
                    list_of_cols.append(col)
                else:
                    dataframe_aborted_cols.append(pd.Series(json[key],name=key))

        dataframe = pd.DataFrame(list_of_cols).T
        cleaned_dataframe = dataframe[['timestamps', 'episode_lengths', 'episode_rewards',
           'episode_winners', 'episode_types']].dropna(axis=0)
        config_and_best = dataframe[['episode_best','config']]
        return cleaned_dataframe, config_and_best

data, config_info = parse_json_2_dataframe(read_json())


def parse_episode_rewards(episode_reward):
    """
           Reads jsons in the specified dir
            Parameters
            ----------
                episode_reward : pd.Series  containing list of lists

            Returns
            -------
                sum(seeker_sum) : int   sum of seeker rewards

                sum(hiding_sum) : int      sum of hiding rewards
        """
    seeker_sum, hiding_sum = [], []
    for frame in episode_reward:
        for seeker_reward, hiding_reward in frame:
            seeker_sum.append(seeker_reward)
            hiding_sum.append(hiding_reward)
    return sum(seeker_sum), sum(hiding_sum)


data.episode_rewards = [parse_episode_rewards(episode_reward) for episode_reward in zip(data.episode_rewards)]
agents_rewards = data.episode_rewards.apply(pd.Series)
data['seeker_rewards'] = agents_rewards[0]
data['hiding_rewards'] = agents_rewards[1]
data.drop('episode_rewards',axis=1,inplace=True)
# data.timestamps = data.timestamps * 1000000000

print(data.columns)

print(data['episode_winners'].value_counts())
print(data[data['episode_winners'] == 'SEEKER']['hiding_rewards'].describe())
