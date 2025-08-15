# Change Vertical Axis To Logarithmic Scale

A tutorial showing how to change a vertical axis to a logarithmic scale in charts in SpreadJS, including UI and code snippets

## Content

Plotting data with large differences in values often leads to incorrect data analysis and may even fail to showcase a completely readable chart. SpreadJS allows users to customize the minimum and the maximum scale values of the vertical axis (also called the value axis). Using this feature, users can change the value axis to a logarithmic scale to meet their specific analytical requirements while formatting charts.

## Usage Scenario

This feature is useful in the following scenarios:

* When the values plotted in a chart cover a huge data range, it's a good idea to change the value axis to a logarithmic scale.
* When business analysts need to carry out an in-depth comparison of sales revenues between different companies.
* When users are trying to visualize comprehensive data sets (like economic, demographic, or marketing data sets).
* When users want to compare the relative change (not the absolute change) in data series values.
* When users want to quickly analyze the variances between significantly different sets of data.

**Example** \- Let's say you want to compare sales revenues of different product\-based companies A and B\, where A refers to a large company that is growing substantially but slowly and B refers to a small company that is growing quickly\.

Now, if the sales revenues of both the companies are depicted in the same line chart, it will just compare the absolute data values and the readability of the chart will decrease to a great extent. Further, it will be difficult to rule out that the smaller firm (B) is growing comparatively faster than the larger one (A). In such a scenario, using log scales helps business analysts to constantly track the sales of competitors easily and effectively.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/spreadjsv13images/log-axes.png)

## LogBase and Scaling Rules

The `scaling` property of the **IAxis** interface allows users to get or set the axes of the chart. The LogBase can be configured to various options - "Null", "10" and "2". While changing the vertical axis to logarithmic axes, the following rules must be kept in mind:

* Users can set the log scale for only the vertical axis (value axis).
* The axes label number grows according to the given base power.
    For example - if the log base is 3, the numbers are 1, 3, 9, 27, 81...
* The minimum base is 2
* LogBase value must lie between 2-1000.
* If the minimum bound is set to auto, the minimum value is 1.

The following table lists the different log base options that can be used while changing the vertical axis to the log scale.

| **LogBase** | **Description** |
| ------- | ----------- |
| Null | This option is used to disable the log scale. |
| 10 | This option is used to customize the log scale with a 10 base. |
| 2 | This option is used to customize the log scale with a 2 base. |

## Supported Chart Types

All chart types containing at least one value axis support logarithmic scaling except Histogram charts, Box & Whisker charts, and Waterfall charts.

> **Note:** The following limitation must be kept in mind while working with log scales in charts:
>
> * If a user enables the log scaled x-axis in a scatter or bubble chart, and then changes the chart type to any other chart type containing a category axis (x-axis); then the chart will display a strange view and the "Add Chart Element Axes" state may not work as expected.

The following code sample depicts a relative comparison of sales revenues of two different companies using logarithmic scaling in the chart.

```javascript
var activeSheet = spread.getActiveSheet();
activeSheet.suspendPaint();
// Prepare data for chart
activeSheet.setValue(0, 1, "Y-2015");
activeSheet.setValue(0, 2, "Y-2016");
activeSheet.setValue(0, 3, "Y-2017");
activeSheet.setValue(0, 4, "Y-2018");
activeSheet.setValue(0, 5, "Y-2019");
activeSheet.setValue(1, 0, "Gradlco Corp. Ltd");
activeSheet.setValue(2, 0, "Saagiate Corp. Ltd.");
activeSheet.setColumnWidth(0, 120);
for (var r = 1; r <= 2; r++)
{
   for (var c = 1; c <= 5; c++) {
   activeSheet.setValue(r, c, parseInt(Math.random() * 5000));
}
}
// Add columnClustered chart
chart_columnClustered = activeSheet.charts.add('chart_columnClustered', GC.Spread.Sheets.Charts.ChartType.columnClustered, 50, 100, 600, 400);
var series = chart_columnClustered.series();
series.add({
   chartType: GC.Spread.Sheets.Charts.ChartType.columnClustered,
   axisGroup: GC.Spread.Sheets.Charts.AxisGroup.primary,
   name: "Sheet1!$A$2",
   xValues: "Sheet1!$B$1:$F$1",
   yValues: "Sheet1!$B$2:$D$2"
});
series.add({
   chartType: GC.Spread.Sheets.Charts.ChartType.lineMarkers,
   axisGroup: GC.Spread.Sheets.Charts.AxisGroup.secondary,
   name: "Sheet1!$A$3",
   xValues: "Sheet1!$B$1:$F$1",
   yValues: "Sheet1!$B$3:$D$3"
});
var axes = chart_columnClustered.axes();
axes.primaryCategory.style.color = 'green';
axes.primaryCategory.title.color = 'green';
axes.primaryCategory.title.text = 'Primary Category Axes';
axes.primaryValue.style.color = 'red';
axes.primaryValue.title.color = 'red';
axes.primaryValue.title.text = 'Primary Value Axes with Logarithmic Scaling';
axes.primaryValue.title.fontSize = 16;
axes.primaryValue.scaling = {
   logBase: 20
};
           
axes.secondaryCategory.visible = true;
axes.secondaryCategory.style.color = 'green';
axes.secondaryCategory.title.color = 'green';
axes.secondaryCategory.title.text = 'Secondary Category Axes';
axes.secondaryCategory.title.fontSize = 16;
axes.secondaryValue.style.color = 'blue';
axes.secondaryValue.title.color = 'blue';
axes.secondaryValue.format = 'General';
axes.secondaryValue.title.text = 'Secondary Value Axes';
chart_columnClustered.axes(axes);
// Configure Chart Title
var title = chart_columnClustered.title();
title.text = "Annual Sales Record";
title.fontFamily = "Cambria";
title.fontSize = 28;
title.color = "Red";
chart_columnClustered.title(title);
activeSheet.resumePaint();
```