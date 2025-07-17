import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Map + KPI 
city_name = "Chicago"
lat, lon = 41.8781, -87.6298
winner = "Verizon"  
kpis = ['Overall', 'Reliability', 'Responsiveness', 'Speed', 'Data', 'Call', 'Text', 'Video']
carriers = ['Verizon', 'AT&T', 'T-Mobile']
kpi_scores = {
    'Overall': [9, 7, 5],
    'Reliability': [8, 6, 9],
    'Responsiveness': [7, 5, 8],
    'Speed': [9, 8, 6],
    'Data': [8, 7, 6],
    'Call': [9, 6, 7],
    'Text': [7, 8, 5],
    'Video': [6, 7, 8]
}
carrier_colors = {
    'Verizon': '#b00000',
    'AT&T': '#067ab4',
    'T-Mobile': '#e60076'
}
fig = make_subplots(
    rows=2, cols=1,
    row_heights=[0.4, 0.6],
    specs=[[{"type": "scattermapbox"}],
           [{"type": "scatter"}]],
    vertical_spacing=0.05,
    subplot_titles=(f"📍{city_name} Market Winner: {winner}", "KPI Performance")
)

# Map 
fig.add_trace(
    go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode='markers+text',
        marker=dict(size=30, color=carrier_colors[winner]),
        text=[f"{winner} Wins"],
        textposition="top center",
        showlegend=False
    ),
    row=1, col=1
)
fig.update_layout(
    mapbox=dict(
        style="carto-positron",
        center={"lat": lat, "lon": lon},
        zoom=10
    ),
)

# KPI Race Chart
y_offsets = list(range(len(kpis), 0, -1)) 
marker_size = 30
halo_size = 40

for y, kpi in zip(y_offsets, kpis):
    # Add horizontal line for each KPI
    fig.add_shape(
        type="line", x0=1, x1=10, y0=y, y1=y, 
        line=dict(color="lightgray", width=2), 
        row=2, col=1)
    
    # Add KPI name as an annotation to the left of the line
    fig.add_annotation(
        x=0.5, y=y, 
        text=f"<b>{kpi}</b>",
        showarrow=False,
        font=dict(size=14),
        xanchor="right", 
        yanchor="middle",
        row=2, col=1
    )

# Carrier icons per KPI
for y, kpi in zip(y_offsets, kpis):
    for carrier in carriers:
        score = kpi_scores[kpi][carriers.index(carrier)]
    
        # Add white halo
        fig.add_trace(go.Scatter(
            x=[score], y=[y],
            mode='markers',
            marker=dict(size=halo_size, color='white'),
            hoverinfo='skip',
            showlegend=False
        ), row=2, col=1)
      
        # Add carrier marker
        fig.add_trace(go.Scatter(
            x=[score], y=[y],
            mode='markers',
            marker=dict(size=marker_size, color=carrier_colors[carrier], line=dict(width=2, color='black')),
            name=carrier,
            showlegend=(y == y_offsets[0])  
        ), row=2, col=1)

# Score bar 
for i in range(1, 11):
    fig.add_annotation(
        x=i, y=0.2,
        text=str(i),
        showarrow=False,
        font=dict(size=12),
        yanchor="top",
        row=2, col=1
    )
fig.add_shape(
    type="line", x0=1, x1=10, y0=0.3, y1=0.3,
    line=dict(color="black", width=1),
    row=2, col=1
)
# Layout Cleanup
fig.update_layout(
    height=700,
    margin=dict(l=100, r=40, t=80, b=40), 
    showlegend=True,
    plot_bgcolor="white",
    mapbox_domain={"x": [0, 1], "y": [0.6, 1]},
)

fig.update_xaxes(
    showticklabels=False, showgrid=False, zeroline=False, visible=False, row=2, col=1
)
fig.update_yaxes(
    showticklabels=False, showgrid=False, zeroline=False, visible=False, row=2, col=1
)

fig.write_image("images/market_test.png", width=1200, height=800, scale=2)
fig.show()

