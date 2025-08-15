# CEILING.MATH

## Content

This function rounds up the given numeral to the nearest multiple of the specified value.

## Syntax

`CEILING.MATH(value, signif, mode)`

## Arguments

This function has the following arguments:

| Argument | Description |
| -------- | ----------- |
| *value* | Refer to the number you want to round off. |
| *signif* | [Optional] Refers to the number representing the rounding factor. |
| *mode* | [Optional] Represents the direction (towards or away from 0) to round negative value. |

By default, significance is +1 for positive numerals and -1 for negative numerals.

## Remarks

Positive numbers with decimal parts are rounded up to the nearest integer.

Negative numbers with decimal parts are rounded up (toward 0) to the nearest integer.

## Data Types

Accepts numeric data for all arguments. Returns numeric data.

## Examples

`CEILING.MATH(14.1,5)` gives the result 15

`CEILING.MATH(26.2)` gives the result 27.

`CEILING.MATH(-14.1,7)` gives the result -14.