#!/usr/bin/env python3
"""Script to enhance Grafana dashboard with additional panels."""
import json

# Load existing dashboard
with open('grafana/dashboards/health-dashboard.json', 'r') as f:
    dashboard = json.load(f)

# Sodium panel (ID: 5, positioned at y=16)
sodium_panel = {
    "datasource": {"type": "influxdb", "uid": "HealthStats"},
    "fieldConfig": {
        "defaults": {
            "color": {"mode": "thresholds"},
            "custom": {
                "axisCenteredZero": False,
                "axisColorMode": "text",
                "axisLabel": "Sodium (mg)",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "drawStyle": "line",
                "fillOpacity": 20,
                "gradientMode": "none",
                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                "lineInterpolation": "smooth",
                "lineWidth": 2,
                "pointSize": 5,
                "scaleDistribution": {"type": "linear"},
                "showPoints": "auto",
                "spanNulls": False,
                "stacking": {"group": "A", "mode": "none"},
                "thresholdsStyle": {"mode": "line"}
            },
            "mappings": [],
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 2000},
                    {"color": "red", "value": 2300}
                ]
            },
            "unit": "short"
        },
        "overrides": []
    },
    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
    "id": 5,
    "options": {
        "legend": {
            "calcs": ["mean", "max"],
            "displayMode": "table",
            "placement": "bottom",
            "showLegend": True
        },
        "tooltip": {"mode": "single", "sort": "none"}
    },
    "targets": [{
        "datasource": {"type": "influxdb", "uid": "HealthStats"},
        "query": 'SELECT mean("sodium_mg") FROM "daily_nutrition" WHERE $timeFilter GROUP BY time(1d) fill(null)',
        "rawQuery": True,
        "refId": "A",
        "resultFormat": "time_series"
    }],
    "title": "Daily Sodium Intake",
    "type": "timeseries",
    "description": "Daily sodium intake with recommended limit (2300mg) as threshold"
}

# Weight vs Calories Correlation panel (ID: 6, positioned at y=16)
correlation_panel = {
    "datasource": {"type": "influxdb", "uid": "HealthStats"},
    "fieldConfig": {
        "defaults": {
            "color": {"mode": "palette-classic"},
            "custom": {
                "axisCenteredZero": False,
                "axisColorMode": "text",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "drawStyle": "line",
                "fillOpacity": 10,
                "gradientMode": "none",
                "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                "lineInterpolation": "smooth",
                "lineWidth": 2,
                "pointSize": 5,
                "scaleDistribution": {"type": "linear"},
                "showPoints": "auto",
                "spanNulls": False,
                "stacking": {"group": "A", "mode": "none"},
                "thresholdsStyle": {"mode": "off"}
            },
            "mappings": [],
            "thresholds": {
                "mode": "absolute",
                "steps": [{"color": "green", "value": None}]
            },
            "unit": "short"
        },
        "overrides": [
            {
                "matcher": {"id": "byName", "options": "Weight (7-day avg)"},
                "properties": [
                    {"id": "color", "value": {"fixedColor": "blue", "mode": "fixed"}},
                    {"id": "custom.axisPlacement", "value": "left"},
                    {"id": "custom.axisLabel", "value": "Weight (lbs)"}
                ]
            },
            {
                "matcher": {"id": "byName", "options": "Calories (7-day avg)"},
                "properties": [
                    {"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}},
                    {"id": "custom.axisPlacement", "value": "right"},
                    {"id": "custom.axisLabel", "value": "Calories"}
                ]
            }
        ]
    },
    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
    "id": 6,
    "options": {
        "legend": {
            "calcs": ["mean", "last"],
            "displayMode": "table",
            "placement": "bottom",
            "showLegend": True
        },
        "tooltip": {"mode": "multi", "sort": "none"}
    },
    "targets": [
        {
            "alias": "Weight (7-day avg)",
            "datasource": {"type": "influxdb", "uid": "HealthStats"},
            "query": 'SELECT moving_average(mean("weight_lbs"), 7) FROM "daily_nutrition" WHERE $timeFilter GROUP BY time(1d) fill(previous)',
            "rawQuery": True,
            "refId": "A",
            "resultFormat": "time_series"
        },
        {
            "alias": "Calories (7-day avg)",
            "datasource": {"type": "influxdb", "uid": "HealthStats"},
            "query": 'SELECT moving_average(mean("calories"), 7) FROM "daily_nutrition" WHERE $timeFilter GROUP BY time(1d) fill(null)',
            "rawQuery": True,
            "refId": "B",
            "resultFormat": "time_series"
        }
    ],
    "title": "Weight vs Calories Correlation",
    "type": "timeseries",
    "description": "Shows how calorie intake correlates with weight changes (7-day moving averages)"
}

# Add new panels
dashboard['panels'].append(sodium_panel)
dashboard['panels'].append(correlation_panel)

# Save enhanced dashboard
with open('grafana/dashboards/health-dashboard.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("✓ Dashboard enhanced with:")
print("  • Sodium intake panel with threshold alerts (2300mg limit)")
print("  • Weight vs Calories correlation panel (7-day averages)")
print("  • Total panels: {}".format(len(dashboard['panels'])))
