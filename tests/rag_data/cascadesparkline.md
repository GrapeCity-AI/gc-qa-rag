# CASCADESPARKLINE

## Content

This function returns a data set used for representing a cascade sparkline.

## Syntax

`CASCADESPARKLINE(pointsRange, pointIndex, [labelsRange, minimum, maximum, colorPositive, colorNegative, vertical, itemTypeRange, colorTotal])`

## Arguments

| Argument | Description |
| -------- | ----------- |
| *pointsRange* | A reference that represents the range of cells that contains values, such as "B2:B8". |
| *pointIndex* | A number or reference that represents the points index. The pointIndex is >= 1 such as 1 or "D2". |
| *labelsRange* | (Optional) A reference that represents the range of cells that contains the labels, such as "A2:A8". The default value is no label. |
| *minimum* | (Optional) A number or reference that represents the minimum values of the display area. The default value is the minimum of the sum (the sum of the points' value), such as -2000.The minimum you set must be less than the default minimum; otherwise, the default minimum is used. |
| *maximum* | (Optional) A number or reference that represents the maximum values of the display area. The default value is the maximum of the sum (the sum of the points' value), such as 6000.The maximum you set must be greater than the default maximum; otherwise, the default maximum is used. |
| *colorPositive* | (Optional) A string that represents the color of the first or last positive sparkline's box (this point's value is positive). The default value is "#8CBF64".If the first or last box represents a positive value, the box's color is set to colorPositive. The middle positive box is set to a lighter color than colorPositive. |
| *colorNegative* | (Optional) A string that represents the color of the first or last negative sparkline's box (this point's value is negative). The default value is "#D6604D".If the first or last box represents the negative value, the box's color is set to colorNegative. The middle negative box is set to a lighter color than colorNegative. |
| *vertical* | (Optional) A boolean that represents whether the box's direction is vertical or horizontal. The default value is FALSE.You must set vertical to true or false for a group of formulas, because all the formulas represent the entire sparkline. |
| *itemTypeRange* | (Optional) An array or reference that represents all the item types of the data range.The values should be {"-", "+", "="} or "A1:A7" that reference the value of {"+", "-", "="}, where "+" indicates positive change, "-" indicates negative change and "=" indicates total columns. |
| *colorTotal* | (Optional) A string that either represents the color of the last sparkline's box when itemTypeRange does not exist or represents the color of the resulting sparkline's box when itemTypeRange exists. |

## Data Types

Returns sparkline.

## Examples

```JavaScript
activeSheet.setFormula(1, 2, '=CASCADESPARKLINE(B2:B8,1,A2:A8,,,"#8CBF64","#D6604D",false)');
```