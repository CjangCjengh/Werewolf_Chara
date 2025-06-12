import plotly.express as px
import pandas as pd

# Define the data for the sunburst chart
data = {
    "Category": [
        "Social Deduction", "Social Deduction", "Social Deduction",
        "Negotiation Skill", "Negotiation Skill", "Negotiation Skill",
        "Multi-Modal Reasoning", "Multi-Modal Reasoning", "Multi-Modal Reasoning",
        "Collaboration / Cooperation", "Collaboration / Cooperation", "Collaboration / Cooperation",
        "Rule Understanding", "Rule Understanding", "Rule Understanding",
        "Divergent Association", "Divergent Association", "Divergent Association",
        "Graph Reasoning", "Graph Reasoning", "Graph Reasoning"
    ],
    "Subcategory": [
        "a", "b", "c",
        "c", "b", "a",
        "g", "k", "d",
        "d", "j", "e",
        "m", "d", "k",
        "k", "e", "d",
        "b", "v", "x"
    ],
    "Count": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Create a sunburst chart
fig = px.sunburst(df, path=['Category', 'Subcategory'], values='Count', title='Board Game Categories')

# Update layout for better appearance
fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

# Show the figure
fig.show()
