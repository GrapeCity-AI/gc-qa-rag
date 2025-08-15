# Cell Value Rule

An explanation of the cell value rule conditional format in SpreadJS

## Content

The cell value rule compares values.
The following code sample creates a cell value rule.

```javascript
var style = new GC.Spread.Sheets.Style();
style.backColor = "red";
var rule = new GC.Spread.Sheets.ConditionalFormatting.NormalConditionRule();
rule.ruleType(GC.Spread.Sheets.ConditionalFormatting.RuleType.cellValueRule);
rule.ranges([new GC.Spread.Sheets.Range(0, 0, 5, 1)]);
rule.operator(GC.Spread.Sheets.ConditionalFormatting.ComparisonOperators.between);
rule.style(style);
rule.value1(2);
rule.value2(100);
activeSheet.conditionalFormats.addRule(rule);
activeSheet.setValue(0, 0, 1, 3);
activeSheet.setValue(1, 0, 45, 3);
```