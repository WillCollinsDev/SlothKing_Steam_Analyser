import pandas as pd
import matplotlib.pyplot as plt
import ast 

FILE_NAME = 'games_march2025_cleaned.csv'

FILE_NAME = 'games_march2025_cleaned.csv'

def run_analysis():
    try:
        df = pd.read_csv(FILE_NAME)
    except FileNotFoundError:
        print(f"Error: Could not find {FILE_NAME}")
        return

    # 1. FIX: Calculate total reviews
    df['total_reviews'] = df['positive'].fillna(0) + df['negative'].fillna(0)

    # 2. FIX: Convert the "Dictionary String" into a clean list of Tag Names
    def extract_tag_names(tag_string):
        try:
            # Turns "{'Puzzle': 1025}" into a real Python dict
            tag_dict = ast.literal_eval(tag_string)
            # Returns just the keys: ['Puzzle', 'Open World', etc.]
            return [str(k).lower().strip() for k in tag_dict.keys()]
        except:
            return []

    print("Processing tags... this may take a second.")
    df['tags_list'] = df['tags'].apply(extract_tag_names)

    # 3. Define your test groups
    test_groups = {
        "Puzzle": ["puzzle"],
        "Detective Puzzle": ["puzzle", "detective"],
        "Horror": ["horror"],
        "Cozy Farm": ["farming sim", "cozy"],
        "RPG": ["rpg"]
    }

    results = []
    for name, required_tags in test_groups.items():
        search_tags = [t.lower() for t in required_tags]
        
        # Check if EVERY search tag exists in the game's tag list
        mask = df['tags_list'].apply(lambda game_tags: 
            all(s_tag in game_tags for s_tag in search_tags)
        )
        
        matched_df = df[mask]
        results.append({
            "Group": name,
            "Count": len(matched_df),
            "Median Reviews": matched_df['total_reviews'].median() if not matched_df.empty else 0
        })

    results_df = pd.DataFrame(results).sort_values(by="Median Reviews", ascending=False)
    print("\n--- 2025 Steam Genre Analysis ---")
    print(results_df.to_string(index=False))

    # 4. Visualization (only if we found data)
    if results_df['Count'].sum() > 0:
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.bar(results_df['Group'], results_df['Count'], color='lightgrey', label='Games')
        ax1.set_ylabel('Number of Games')
        plt.xticks(rotation=45)
        
        ax2 = ax1.twinx()
        ax2.plot(results_df['Group'], results_df['Median Reviews'], color='blue', marker='o', label='Median Success')
        ax2.set_ylabel('Median Reviews')
        
        plt.title('Supply vs. Success (Dictionary Tag Data)')
        plt.tight_layout()
        plt.show()
    else:
        print("Still no matches found. Double-check your tag spelling!")

if __name__ == "__main__":
    run_analysis()