import os
import json
import matplotlib.pyplot as plt

# Elo rating update parameters
K = 32

def calculate_elo(winner_ratings, loser_ratings):
    # Calculate the average ratings
    avg_winners_rating = sum(winner_ratings) / len(winner_ratings)
    avg_losers_rating = sum(loser_ratings) / len(loser_ratings)

    # Calculate expected scores
    expected_winner_score = 1 / (1 + 10 ** ((avg_losers_rating - avg_winners_rating) / 400))
    expected_loser_score = 1 - expected_winner_score

    # Update the ratings
    for i in range(len(winner_ratings)):
        winner_ratings[i] += K * (1 - expected_winner_score)
    for i in range(len(loser_ratings)):
        loser_ratings[i] += K * (0 - expected_loser_score)
        
    return winner_ratings, loser_ratings

def main():
    # Path to the folder
    folder_path = "logs/werewolf"

    # Initialize elo ratings
    elo_ratings = {}
    initial_rating = 1000

    # Iterate over all json files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)

            # Open and read the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)
                winners = data['winners']
                losers = data['losers']

                # Initialize players' ratings if not already present
                for player in data['players']:
                    if player not in elo_ratings:
                        elo_ratings[player] = initial_rating

                # Update elo ratings
                winner_ratings = [elo_ratings[player] for player in winners]
                loser_ratings = [elo_ratings[player] for player in losers]
                
                updated_winner_ratings, updated_loser_ratings = calculate_elo(winner_ratings, loser_ratings)

                # Assign updated ratings back
                for i, player in enumerate(winners):
                    elo_ratings[player] = updated_winner_ratings[i]
                for i, player in enumerate(losers):
                    elo_ratings[player] = updated_loser_ratings[i]

    # Sort players by their Elo ratings in descending order
    sorted_players = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
    players = [player for player, _ in sorted_players]
    scores = [score for _, score in sorted_players]

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.bar(players, scores, color='lightblue')
    # plt.xlabel('Players')
    plt.ylabel('Elo Ratings')
    plt.title('Player Elo Ratings')
    plt.xticks(rotation=45)

    # Set y-axis limits
    plt.ylim(min(scores) - 50, max(scores) + 50)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()