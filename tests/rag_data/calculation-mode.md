# Calculation Mode

An explanation of the calculation modes available in SpreadJS, including auto and manual, calculation types, calculation methods, and code snippets

## Content

SpreadJS automatically updates formulas when the dependent values (cells, values, or names referenced in a formula) change. However, you can switch automatic calculations to manual if you want to control when the formulas are recalculated and not as soon as changes are made to any referenced cells. The `CalculationMode` enumeration in the SpreadJS API allows you to set calculation options as auto or manual.
When the `CalculationMode` is set to **auto**, which is the default mode, SpreadJS automatically calculates all dirty cells every time the referenced cells are changed. For example, during copy-paste or cell input. Note that SpreadJS considers the cells as dirty when the cells are changed and need recalculation consequently.
On the other hand, when the `CalculationMode` is set to **manual**, SpreadJS will only calculate and update the formulas when you explicitly request it. This can be useful in situations where you have a large worksheet with many complex formulas, and you want to avoid frequent recalculations to improve performance and responsiveness. For example, SpreadJS resets the formula and the cell value during the cut or copy-paste of a value, but it doesn't recalculate any formulas.

> **Note**: SpreadJS supports the CalculationMode option on exporting to Excel.

The following code sample shows how to set the manual calculation option when initializing the workbook.

```javascript
// Switch to manual mode when initializing the workbook.
var spread = new GC.Spread.Sheets.Workbook(document.getElementById("ss"), {calculationMode: GC.Spread.Sheets.CalculationMode.manual});

Or

spread.options.calculationMode = GC.Spread.Sheets.CalculationMode.manual;
```

Once you switch to manual calculation mode, you need to manually update the formulas in the worksheet using the `calculate()` method which accepts the `CalculationType` enum value as a parameter.
The `CalculationType` enumeration specifies the calculation type. The available members of this enumeration are mentioned below.

| **Member** | **Description** |
| ------ | ----------- |
| all | Marks all cells, which are in the range, as dirty for calculation.<br>This is the default calculation type. |
| rebuild | Rebuilds all the formulas in the range and then marks them as dirty for calculation. |
| minimal | Marks the formulas as dirty but does not mark the volatile and circular reference cells as dirty for calculation. |
| regular | Marks the volatile cells and circular reference cells as dirty for calculation. |

Look at the table below to understand SpreadJS’s behavior when utilizing automatic and manual calculation modes with various formulas and their dependencies.

| **Used Formula** | **Automatic (Default mode)** | **Manual** |
| ------------ | ------------------------ | ------ |
| suspendCalcService(true) | @cols=2:Disable the calculation engine and do not recalculate any cell. |
| resumeCalcService(false) | Enable the calculation engine and calculate volatile cells, circular reference cells, and dirty cells. | Enable the calculation engine and mark the volatile cells as dirty, but don’t calculate the dirty cells. |
| resumeCalcService(true) | Enable the calculation engine and calculate all cells. | Enable the calculation engine, mark all the cells as dirty, but don’t calculate the dirty cells. |
| resumeCalcService(false)<br>and<br>sheet.setFormula | Calculate the formulas and their dependencies. | Calculate the formulas. |
| resumeCalcService(false)<br>and<br>spread.calculate() | @cols=2:Calculate all formulas in all open worksheets. |
| resumeCalcService(false)<br>and<br>spread.calculate(GC.Spread.Sheets.CalculationType.regular) | @cols=2:Calculate all cells that are marked as dirty, that is, cells that are dependent on volatile or changing data, as well as cells that are programmatically marked as dirty. |
| resumeCalcService(false)<br>and<br>spread.calculate(GC.Spread.Sheets.CalculationType.rebuild) | @cols=2:Rebuild all formulas in the spread, then calculate them. |
| resumeCalcService(false)<br>and<br>spread.calculate(null, “Sheet1“) | Mark all formulas in Sheet 1 to dirty and then dirty dependencies out of the range.<br>Calculate all dirty cells. | Mark all formulas in Sheet 1 to dirty and then dirty dependencies out of the range.<br>Calculate dirty cells in Sheet 1.<br>Keep other cells in dirty state. |

> **Note**: For recalculating formulas in cells, the existing sheet.recalcAll() method has been deprecated from the SpreadJS v16.2 release. Instead of this, you can use spread.calculate() for higher versions.

The following code samples show various calculations using different calculation modes and types in SpreadJS.

```javascript
spread.sheets[0].setFormula(0,0,"RAND()");
spread.sheets[0].setFormula(1,0,"=Sheet2!A1");
spread.sheets[0].setFormula(2,0,"=1+2"); 
spread.sheets[1].setFormula(0,0,"RAND()"); 
spread.sheets[1].setFormula(1,0,"=Sheet1!A1");

// All the cell is recalculated. 
spread.calculate(); spread.calculate(GC.Spread.Sheets.CalculationType.regular); 

// Sheet1!A1 Sheet2!A2 are evaluated to new number, and Sheet1!A2 Sheet1!A3 are evaluated. 
spread.calculate(GC.Spread.Sheets.CalculationType.all, "Sheet1"); 

// Sheet1!A1 Sheet2!A2 are evaluated to new number. 
spread.calculate(GC.Spread.Sheets.CalculationType.regular, "Sheet1!A1"); 

// No cells are evaluated.
spread.calculate(GC.Spread.Sheets.CalculationType.regular, "Sheet1!A2"); 

// Sheet1!A1 is evaluated to new number, Sheet1!A2 Sheet1!A3 are evaluated but don't changed, Sheet2!A2 keeps dirty in manual mode. 
spread.calculate(GC.Spread.Sheets.CalculationType.all, "Sheet1"); 

// Sheet1!A1 is evaluated to new number, Sheet2!A2 keeps dirty in manual mode. 
spread.calculate(GC.Spread.Sheets.CalculationType.regular, "Sheet1"); 

// Sheet2!A2 is evaluated because it is dirty. 
spread.calculate(GC.Spread.Sheets.CalculationType.minimal);
```

## Using Designer

You can set the required calculation options using SpreadJS Designer by selecting the '**Calculation Options**' button available inside the FORMULAS > Calculations tab group.

![CalculationOptions](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/CalculationOptions.48415b.png?width=1090)

In the case of manual calculation mode, you need to select which section of the workbook you would like to be recalculated.

* Click the **Calculate Now** button to update changes across all open worksheets.

![CalculateNow](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/CalculateNow.e35c34.gif?width=1000)

* Click the **Calculate Sheet** button if you only want the modifications to be reflected in the same worksheet.

![CalculateSheet](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/CalculateSheet.389d98.gif?width=1000)