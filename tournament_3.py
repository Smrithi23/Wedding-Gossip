import argparse
from wedding_gossip import WeddingGossip
import pandas as pd

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--teams", "-teams", default=[1,2], nargs="+", help="Helper Text")
    parser.add_argument("--seed", "-s", default=2, help="Seed")
    parser.add_argument("--scale", "-sc", default=9, help="Scale")
    parser.add_argument("--turns", "-T", default=1440, help="Number of turns")
    parser.add_argument("--gui", "-g", default="False", help="GUI")
    parser.add_argument("--interval", "-i", default=1, help="GUI")
    args = parser.parse_args()

    # configuration 3
    df = pd.DataFrame(columns=["Run", "Seed", "Turns", "Team Number", "Team Score", "Group Score"])
    df.to_csv("config_3.csv")
    run = 1
    seeds = [1, 2, 3]
    turns = [10, 30, 60, 120, 180, 360, 1024, 1440]
    groups = [[1], [2], [3], [4], [5], [6]]
    for seed in seeds:
        for turn in turns:
            for group in groups:
                try:
                    print(run, seed, turn, group)
                    args.teams=group
                    args.seed=seed
                    args.turns=turn
                    args.scale=10
                    args.gui="False"
                    args.interval=1
                    args.run=run
                    wedding_game = WeddingGossip(args)

                    row = [run, seed, turns]

                    results = wedding_game.get_results()
                    team_scores = list(results["team_scores"].values())
                    group_score = results["group_score"]
                    row = [run, seed, turn, group[0], team_scores[0], group_score]
                    df = pd.DataFrame([row], columns=["Run", "Seed", "Turns", "Team Number", "Team Score", "Group Score"])
                    df.to_csv("config_3.csv", mode='a', header=False)
                except:
                    row = [run, seed, turn, 'Error', 'Error', 'Error']
                    df = pd.DataFrame([row], columns=["Run", "Seed", "Turns", "Team Number", "Team Score", "Group Score"])
                    df.to_csv("config_3.csv", mode='a', header=False)
                run += 1