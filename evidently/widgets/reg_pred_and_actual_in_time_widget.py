#!/usr/bin/env python
# coding: utf-8

import json
from typing import Optional

import pandas as pd
import numpy as np

import plotly.graph_objs as go

from evidently import ColumnMapping
from evidently.analyzers.regression_performance_analyzer import RegressionPerformanceAnalyzer
from evidently.model.widget import BaseWidgetInfo
from evidently.widgets.widget import Widget, RED, GREY


class RegPredActualTimeWidget(Widget):
    def __init__(self, title: str, dataset: str = 'reference'):
        super().__init__(title)
        self.dataset = dataset  # reference or current

    def analyzers(self):
        return [RegressionPerformanceAnalyzer]

    def calculate(self,
                  reference_data: pd.DataFrame,
                  current_data: Optional[pd.DataFrame],
                  column_mapping: ColumnMapping,
                  analyzers_results) -> Optional[BaseWidgetInfo]:
        results = analyzers_results[RegressionPerformanceAnalyzer]

        if results['utility_columns']['target'] is None or results['utility_columns']['prediction'] is None:
            if self.dataset == 'reference':
                raise ValueError(f"Widget [{self.title}] requires 'target' and 'prediction' columns")
            return None
        if self.dataset == 'current':
            dataset_to_plot = current_data.copy(deep=False) if current_data is not None else None
        else:
            dataset_to_plot = reference_data.copy(deep=False)

        if dataset_to_plot is None:
            if self.dataset == 'reference':
                raise ValueError(f"Widget [{self.title}] requires reference dataset but it is None")
            return None

        dataset_to_plot.replace([np.inf, -np.inf], np.nan, inplace=True)
        dataset_to_plot.dropna(axis=0, how='any', inplace=True)

        # make plots
        pred_actual_time = go.Figure()

        target_trace = go.Scatter(
            x=dataset_to_plot[results['utility_columns']['date']] if results['utility_columns'][
                'date'] else dataset_to_plot.index,
            y=dataset_to_plot[results['utility_columns']['target']],
            mode='lines',
            name='Actual',
            marker=dict(
                size=6,
                color=GREY
            )
        )

        pred_trace = go.Scatter(
            x=dataset_to_plot[results['utility_columns']['date']] if results['utility_columns'][
                'date'] else dataset_to_plot.index,
            y=dataset_to_plot[results['utility_columns']['prediction']],
            mode='lines',
            name='Predicted',
            marker=dict(
                size=6,
                color=RED
            )
        )

        zero_trace = go.Scatter(
            x=dataset_to_plot[results['utility_columns']['date']] if results['utility_columns'][
                'date'] else dataset_to_plot.index,
            y=[0] * dataset_to_plot.shape[0],
            mode='lines',
            opacity=0.5,
            marker=dict(
                size=6,
                color='green',
            ),
            showlegend=False,
        )

        pred_actual_time.add_trace(target_trace)
        pred_actual_time.add_trace(pred_trace)
        pred_actual_time.add_trace(zero_trace)

        pred_actual_time.update_layout(
            xaxis_title="Timestamp" if results['utility_columns']['date'] else "Index",
            yaxis_title="Value",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        pred_actual_time_json = json.loads(pred_actual_time.to_json())

        return BaseWidgetInfo(
            title=self.title,
            type="big_graph",
            size=1,
            params={
                "data": pred_actual_time_json['data'],
                "layout": pred_actual_time_json['layout']
            },
        )
