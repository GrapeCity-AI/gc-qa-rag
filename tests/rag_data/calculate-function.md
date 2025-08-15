# CALCULATE

## Content

This function can be used to expand the group context when summarizing at the group level of a TableSheet. This function expands the context for the formula represented by the first argument.

## Syntax

`=CALCULATE (formula_string, expand_context)`

## Arguments

This function has these arguments:

| Argument | Description |
| -------- | ----------- |
| *formula\_string* | [Required] The formula evaluates with the context from expand\_context. |
| *expand\_context* | [Required] The expand\_context is from REMOVEFILTERS. |

## Remarks

The CALCULATE function should only be used in the `formula` property of `summaryFields` option in a groupBy method.

## Data Types

Accepts a numeric value. Returns a numeric value.

## Examples

The following sample code shows the basic usage of the CALCULATE function.

```JavaScript
sheet.groupBy([
    {
        caption: "Ship Via", field: `ShipVia`, width: 160,
        summaryFields: [
            {
                caption: "Ratio of Year Quarter", width: 170, style: { formatter: "0.00%" },
                formula: `=SUM([Freight]) / CALCULATE( SUM([Freight]), REMOVEFILTERS("ShipVia"))`, // ratio of sum of freight under freight level to sum of freight under ship name
            }
        ]
    }
])
```