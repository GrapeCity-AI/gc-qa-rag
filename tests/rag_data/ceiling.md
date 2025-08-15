# CEILING

## Content

This function rounds a number up to the nearest multiple of a specified value.

## Syntax

`CEILING(value, signif)`

## Arguments

This function has these arguments:

| Argument | Description |
| -------- | ----------- |
| *value* | Number to round |
| *signif* | Number representing the rounding factor |

Use either both positive or both negative numbers for the arguments. Regardless of the sign of the numbers, the value is rounded away from zero.

## Data Types

Accepts numeric data for both arguments. Returns numeric data.

## Examples

`CEILING(C4,B2)`

`CEILING(B3,0.05)`

`CEILING(R4C3,1)`

`CEILING(4.65,2)` gives the result 6

`CEILING(-2.78,-1)` gives the result -3