# Cell References in a Formula

## Content

A formula can refer to constant values or cell references. If a value in any of the referenced cells changes, the result of the formula changes. If you use constant values in the formula instead of references to the cells, the result changes only if you modify the formula (or values in the formula).
With SpreadJS, you can convert the specific cell range to a formula string using the [formulaToRanges](gcdocsite__documentlink?toc-item-id=3db14618-6aaf-4198-b174-826a09082d17#formulaToRanges) method. For instance - returning an "A1" address from the row and column numbers.
For more information on using cell references in a formula, refer to [Use Cell References](gcdocsite__documentlink?toc-item-id=1af17061-d0a8-4ccb-8d8a-c12834c9e860).
If a new row is added right before or after a cell range in a formula then the range does not include the new row.
The following topics describe the different notation styles and reference types:

* A1 Notation
* R1C1 Notation
* Relative and Absolute

## A1 Notation

Each cell can be referenced by a combination of its column letter (A through Z, then AA to ZZ, AAA to ZZZ, etc.) and row number (1 and beyond) for a total of 2,147,483,648 rows and columns. For example, D50 refers to the cell at the intersection of column D and row 50. To refer to a range of cells, enter the reference for the cell in the upper-left corner of the range, a colon (:), and then the reference to the cell in the lower-right corner of the range.

## R1C1 Notation

Each cell can be referenced by its row and column number by preceding each by the letter "R" for row and the letter "C" for column. For example, R1C3 is the cell in the first row and third column.

| A1 Cell Ref. | R1C1 Cell Ref. | Description |
| ------------ | -------------- | ----------- |
| B12 | R12C2 | Cell in the second column (column B) and twelfth row (row 12) |
| D14:D48 | R14C4:R48C4 | The range of cells in the fourth column (column D) and rows 14 through 48 |
| E16:H16 | R16C5:R16C8 | The range of cells in the sixteenth row (row 16) in the fifth through the eighth column (columns E through H) |
| A25:E70 | R25C1:R70C5 | The range of cells in the first five columns (columns A through E) and rows 25 through 70 |

## Relative and Absolute

A relative cell reference is a reference to a cell relative to the position of the cell with the formula. An absolute reference is a cell reference that always refers to a cell by its exact location in the sheet and not concerning the present cell.
Relative references are automatically adjusted when you copy them, but absolute references are not. The widget can use absolute or relative cell references. You can set the cell reference style for a workbook by using the [referenceStyle ](gcdocsite__documentlink?toc-item-id=cbd0a51d-62f0-48b0-8fb7-1855088c327f)property. The formula does not support a range reference that contains both absolute and relative row or column references. In other words, the start and end rows in a range reference have to match (both absolute or both relative).
The following table contains examples of valid relative cell references in formulas.

| Function | Description |
| -------- | ----------- |
| SUM(A1:A10) | Sums row 1 through 10 in the first column |
| PI( )\*C6 | Multiplies pi times the value in cell C6 |
| (A1 + B1) \* C1 | Adds the values in the first two cells and multiplies the result by the value in the third cell |
| IF(A1>5, A1\*2, A1\*3) | Checks if the contents of cell A1 are greater than 5, and if so, multiply the contents of cell A1 by 2, or else multiply the contents of cell A1 by 3 |

For A1 notation, use a dollar sign ($) preceding the row or column (or both) to indicate an absolute reference. For example

| A1 Cell Ref. | Description |
| ------------ | ----------- |
| $A$1 | absolute first column, absolute first row |
| $A1 | absolute first column, relative row plus one |
| A$1 | relative column plus one, absolute first row |
| A1 | relative column plus one, relative row plus one |

For R1C1 notation, use brackets [ ] around the row or column number (or both) to indicate a relative reference. For example

| R1C1 Cell Ref. | Description |
| -------------- | ----------- |
| R1C1 | absolute first row, absolute first column |
| R1C[1] | absolute first row, relative column plus one |
| R[1]C1 | relative row plus one, absolute first column |
| R[1]C[1] | relative row plus one, relative column plus one |
| R[-1]C[-1] | relative row minus one, relative column minus one |

In this notation, the number inside the brackets is an offset from the current cell. This number may be a negative or positive integer or zero. Leaving off the offset entirely is a short-hand way of indicating a zero offset. So,
RC2 is equivalent to `R[0]C2`
`R[3]C` is equivalent to `R[3]C[0]`

## Dynamic References

SpreadJS provides the **dynamicReferences** flag to support minimal memory usage and better performance while using calculation-related formula functions. With this flag, the process of calculation using formula functions across worksheets becomes faster.
The dynamicReferences flag accepts Boolean values to enable or disable the dynamic reference mode for CalcEngine. It helps in enhancing the performance of formula functions like IF, CHOOSE, SUMIF, SUMIFS, AVERAGEIF, AVERAGEIFS, MAXIFS, MINIFS, COUNTIFS, VLOOKUP, and HLOOKUP.
By default, the value for the **dynamicReferences** flag is true. To increase the performance of calculations, the flag should be set to false.

> **Note**: The **dynamicReferences** flag should be set before setting the formula or fromJSON.

<span lang="EN-US" style="font-family:Consolas;mso-fareast-font-family:
Consolas;mso-bidi-font-family:Consolas">The following code snippet shows how the circular reference gets affected when dynamicReferences option is set to false or true.</span>

```JavaScript
spread.options.dynamicReferences = false;
spread.options.iterativeCalculation = false;
sheet.setFormula(0, 1, '=SUMIF(A:A,"a*",B:B)');
sheet.setValue(1, 0, "aaa");
sheet.setValue(1, 1, 123); // Here, formula B1 result won't change. Because B1 have listener of A:A, B:B, it's circular reference and iterativeCalculation is false.

spread.options.dynamicReferences = true;
spread.options.iterativeCalculation = false;
sheet.setFormula(0, 1, '=SUMIF(A:A,"a*",B:B)');
sheet.setValue(1, 0, "aaa");
sheet.setValue(1, 1, 123); // Here, formula B1 result will change. Because B1 have listener of A:A, B2, not B:B, it's not circular reference, can calculate when the iterativeCalculation is false
```